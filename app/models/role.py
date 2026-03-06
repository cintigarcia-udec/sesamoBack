from sqlalchemy import Boolean, Column, TIMESTAMP, Integer, String, func
from app.utilities.db import Base


class Role(Base):
  __tablename__ = 'roles'

  id = Column(Integer, primary_key=True, index=True)
  name = Column(String(50), nullable=False)
  created_at = Column(TIMESTAMP(timezone=True), default=func.now(), nullable=True)
  updated_at = Column("updated_at", TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

  def to_dict(self):
    return {
      "id": self.id,
      "name": self.name,
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }
