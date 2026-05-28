from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Cite(Base):
    __tablename__ = "cites"

    id             = Column(Integer, primary_key=True, index=True)
    nom            = Column(String(150), nullable=False)
    description    = Column(String(500), default="")
    lieu           = Column(String(150), default="")
    localisation   = Column(String(100), default="")  # coordonnées GPS
    note           = Column(Float, default=5.0)
    image_path     = Column(String(300), nullable=True)
    responsable_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    updated_at     = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    responsable = relationship("User", back_populates="cites")
    chambres    = relationship("Chambre", back_populates="cite", cascade="all, delete-orphan")
    locataires  = relationship("Locataire", back_populates="cite")
    annonces    = relationship("Annonce", back_populates="cite", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Cite id={self.id} nom={self.nom}>"
