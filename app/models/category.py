from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func

from app.utilities.db import Base

class Category(Base):
  __tablename__ = 'categories'

  id = Column("id", Integer, primary_key=True, index=True)
  name = Column("name", String(255))
  created_at = Column("created_at", TIMESTAMP(timezone=True), default=func.now())
  updated_at = Column("updated_at", TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

  def to_dict(self) -> dict:
    return {
      "id": self.id,
      "name": self.name,
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None
    }