import json
from contextlib import closing
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Request
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.models.sysLogs import SystemLogs
from app.utilities.db import get_session
from app.utilities.logger import logger
from app.utilities.timezone import bogota_tz

def save_log_entry(
  request: Request,
  duration: Optional[float],
  payload: Optional[Any],
  status_code: int,
  response: Optional[str] = None,
  error_detail: Optional[str] = None
):
  """
  Registra un log de la solicitud HTTP.

  Args:
    request (Request): El objeto request de FASTAPI.
    duration (float): Duración de la solicitud.
    payload (Any): El cuerpo de la solicitud enviada.
    status_code (int): El código de estado HTTP de la respuesta.
    response (str): La respuesta retornada por el servicio, una vez llamado.
    error_detail (str): Detalle de la excepción ocurrida, si aplica.

  Raises:
    Exception: Si ocurre un error en el guardado de log.
  """
  if settings.logs_path is None:
    raise Exception("Logs path is not configured in settings.")

  log_entry = {
    "user_id": request.state.current_user.id if getattr(request.state, 'current_user', None) else None,
    "payload": payload,
    "url": request.url._url,
    "http_method": request.method,
    "duration": duration,
    "origin_ip": request.client.host if request.client else None,
    "user_agent": request.headers.get("user-agent"),
    "response": response or error_detail,
    "http_status": status_code,
    "creation_date": datetime.now(tz=bogota_tz),
  }

  try:
    with closing(next(get_session('sesamo'))) as session:
      temp_log = SystemLogs(**log_entry)
      logger.info('start saving SystemLogs')
      session.add(temp_log)
      session.commit()
      logger.info('finishing saving SystemLogs')
      session.close()
  except Exception as e:
    logger.error(f"Error saving SystemLogs: {e}")

async def log_exception(
  request: Request,
  exc: Exception,
  status_code: int,
  response_content: Optional[Any] = None
):
  """
  Guarda en `system_logs` la información de una excepción.

  Este helper es utilizado por los manejadores globales de excepciones para
  estandarizar el registro de errores a nivel de endpoint.
  """
  payload = getattr(request.state, "system_log_payload", None)
  start_time = getattr(request.state, "system_log_start_time", None)
  duration = None

  if start_time:
    duration = (datetime.now(timezone.utc) - start_time).total_seconds()

  response_payload = response_content

  if response_payload is None:
    detail = getattr(exc, "detail", None)
    
    if isinstance(detail, (str, dict, list)):
      response_payload = {"detail": detail}
    elif hasattr(exc, "errors"):
      try:
        response_payload = {"detail": exc.errors()}
      except Exception:
        response_payload = None

  if response_payload is None:
    response_payload = {"detail": "Internal server error"}

  if isinstance(response_payload, str):
    response_message = response_payload
  else:
    try:
      response_message = json.dumps(response_payload)
    except TypeError:
      response_message = str(response_payload)

  root_exc = exc.__cause__ if getattr(exc, "__cause__", None) else exc
  error_detail = str(root_exc)

  await run_in_threadpool(
    save_log_entry,
    request,
    duration,
    payload,
    status_code,
    response_message,
    error_detail
  )