import pytz
from datetime import datetime

bogota_tz = pytz.timezone('America/Bogota')


def get_local_now() -> datetime:
  """R
  etorna la hora actual en la zona horaria de Bogotá.
  """
  return datetime.now(bogota_tz)


def get_local_now_naive() -> datetime:
  """
  Fuerza la hora local sin timezone info
  """
  bogota_time = datetime.now(bogota_tz)
  
  return bogota_time.replace(tzinfo=None)  # Quita el timezon