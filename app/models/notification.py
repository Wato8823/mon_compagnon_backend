from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class NotifType(str, enum.Enum):
    bailExpire        = "bailExpire"
    bailBientotExpire = "bailBientotExpire"
    annonce           = "annonce"
    info              = "info"


class Notification(Base):
    __tablename__ = "notifications"

    id      = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    titre   = Column(String(200), nullable=False)
    message = Column(String(500), nullable=False)
    type    = Column(Enum(NotifType), default=NotifType.info, nullable=False)
    lue     = Column(Boolean, default=False)
    ref_id  = Column(String(50), nullable=True)   # ID de l'annonce / locataire référencé
    date    = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification id={self.id} user_id={self.user_id} type={self.type}>"
