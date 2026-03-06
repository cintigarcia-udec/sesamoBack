import uvicorn
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import *
from app.helpers.logs import log_exception
from app.utilities.db import initialize_database
from app.routers import (
    users,
    schools,
    roles,
    categories,
    questionnaires,
    questions,
    answer_options,
    user_responses,
    auth
)

async def lifespan(app: FastAPI):
  if settings.environment == 'development':
    initialize_database()
  yield

app = FastAPI(
  lifespan=lifespan,
  title="Sesamo API",
  version="0.0.1",
  root_path=settings.root_path,
  swagger_ui_parameters={
    "syntaxHighlight": {"theme": "tomorrow-night"},
    "deepLinking": False,
    "filter": True
  }
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=settings.allowed_origins.split(","),
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(schools.router)
app.include_router(roles.router)
app.include_router(categories.router)
app.include_router(questionnaires.router)
app.include_router(questions.router)
app.include_router(answer_options.router)
app.include_router(user_responses.router)

@app.get("/")
async def read_root():
  return {"message": "Welcome to the FastAPI backend!"}

@app.middleware("http")
async def capture_request(request: Request, call_next):
  """
  Middleware para capturar solicitudes HTTP y registrar información relevante.
  Args:
    request (Request): La solicitud HTTP entrante.
    call_next (Callable): Función para pasar la solicitud al siguiente middleware o ruta.
  Returns:
    Response: La respuesta HTTP generada por el siguiente middleware o ruta.
  """
  # Excluir rutas de WebSocket del middleware
  if request.url.path.startswith("/api/ws/") or request.url.path.startswith("/api/v1/ws/"):
    return await call_next(request)
  
  start_time = datetime.now(timezone.utc)

  # Capturar el cuerpo de la solicitud para reutilizarlo
  body_bytes = await request.body()
  body_text = body_bytes.decode("utf-8", errors="ignore") if body_bytes else None

  async def receive_body():
    return body_bytes
  
  # Inicializar variables
  parsed_form = None

  # Detectar tipo de contenido de la solicitud
  content_type = request.headers.get("content-type", "")

  if "multipart/form-data" in content_type:
    # Leer y procesar form-data
    form_data = await request.form()
    parsed_form = {name: value for name, value in form_data.items() if not hasattr(value, "filename")}
  elif "application/json" in content_type:
    try:
      parsed_form = await request.json()
    except Exception:
      parsed_form = None

  request = Request(request.scope, receive_body)
  request.state.system_log_start_time = start_time
  payload_for_log = None

  if request.method in {"POST", "PUT", "PATCH"} and 'auth' not in str(request.url):
    payload_for_log = parsed_form if parsed_form else body_text

  request.state.system_log_payload = payload_for_log

  try:
    response = await call_next(request)
  except HTTPException as exc:
    content = {"detail": exc.detail}
    await log_exception(request, exc, exc.status_code, content)
    raise
  except RequestValidationError as exc:
    content = {"detail": exc.errors()}
    await log_exception(request, exc, status.HTTP_422_UNPROCESSABLE_ENTITY, content)
    raise
  except Exception as exc:
    content = {"detail": "Internal server error"}
    await log_exception(request, exc, status.HTTP_500_INTERNAL_SERVER_ERROR, content)
    raise

  # Calcular la duración y registrar los datos
  duration = (datetime.now(timezone.utc) - start_time).total_seconds()
  if "/api" in str(request.url) or '/notification' in str(request.url):
    payload = (parsed_form if parsed_form else body_text) if ( request.method == "POST" and 'auth' not in str(request.url) ) else None
    content = None
    response_content = None
    content = b""

    async for chunk in response.body_iterator:
      content += chunk
    
    # Crear una nueva respuesta con el contenido capturado
    response = Response(
      content=content,
      status_code=response.status_code,
      headers=dict(response.headers),
      media_type=response.media_type,
    )

  return response

def on_starting(server):
  """
  Función que se ejecuta al iniciar el servidor Gunicorn (proceso Master).
  Se encarga de la inicialización de la base de datos antes de hacer fork.
  """
  print("Starting Gunicorn server...")
  from app.utilities.db import initialize_database, DatabaseConnectionPool
  initialize_database()
  
  # Limpiar el pool en el Master para que los workers no hereden sockets abiertos
  DatabaseConnectionPool().dispose_all()

def post_fork(server, worker):
  """
  Hook que se ejecuta en cada worker después del fork de Gunicorn.
  Asegura que cada worker empiece con una instancia limpia del pool.
  """
  from app.utilities.db import DatabaseConnectionPool
  
  DatabaseConnectionPool().dispose_all()

if __name__ == "__main__":
  uvicorn.run(
    app,
    host='0.0.0.0',
    port=8000
  )