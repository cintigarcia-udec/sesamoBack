import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from app.config import settings

# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
  level=settings.logging_level,
  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
  handlers=[
    RotatingFileHandler(
      log_dir / "app.log",
      maxBytes=1024 * 1024 * 5,  # 5 MB
      backupCount=3
    ),
    logging.StreamHandler()
  ]
)

logger = logging.getLogger("app")