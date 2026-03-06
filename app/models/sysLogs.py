from sqlalchemy import Column, TIMESTAMP, Float, ForeignKey, Integer, String, Text
from datetime import datetime
from app.utilities.db import Base
from app.utilities.timezone import bogota_tz

class SystemLogs(Base):
  """
  Representa una entrada de registro en la base de datos.

  Attributes:
    id (int): Identificador único.
    user_id (str): Número que referencia el id de un usuario, no es FK (opcional).
    url (str): URL llamada.
    payload (str): Carga útil de la solicitud.
    http_method (str): Método HTTP del servicio.
    http_status (str): Código de estado HTTP en la respuesta.
    response (str): Respuesta del servicio llamado.
    duration (float): Duración de obtención de la respuesta en ms.
    origin_ip (str): IP desde donde se realizó la solicitud.
    user_agent (str): Cliente utilizado para la solicitud.
    created_at (datetime): Marca de tiempo cuando se creó el registro.
  """

  __tablename__ = 'system_logs'

  id = Column(Integer, primary_key=True, index=True)
  user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
  url = Column(String(255), nullable=False)
  payload = Column(Text)
  http_method = Column(String(10), nullable=False)
  http_status = Column(Integer, nullable=False)
  response = Column(Text)
  duration = Column(Float, nullable=True)
  origin_ip = Column(String(45), nullable=True)  
  user_agent = Column(Text, nullable=True)
  creation_date = Column(TIMESTAMP(timezone=True), default=datetime.now(tz=bogota_tz))
