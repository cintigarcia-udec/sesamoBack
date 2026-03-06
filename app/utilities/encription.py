
import json
import bcrypt
from fernet import Fernet
from app.config import settings

cipher = Fernet(settings.ENCRYPTION_KEY)

def encrypt_data(data: dict) -> str:
  """
  Encripta un diccionario y lo convierte en una cadena.
    
  Args:
    data (dict): El diccionario a encriptar.
  Returns:
    str: La cadena encriptada.
  """
  return cipher.encrypt(json.dumps(data).encode()).decode()

def decrypt_data(encrypted_data: str) -> any:
  """
  Desencripta una cadena y la convierte en un diccionario.
    
  Args:
    encrypted_data (str): La cadena encriptada a desencriptar.
  Returns:
    dict: El diccionario desencriptado.
  """
  return eval(cipher.decrypt(encrypted_data.encode()).decode())


def verify_password(plain_password: str, hashed_password: str) -> bool:
  return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))