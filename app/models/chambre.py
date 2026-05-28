from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class EtatChambre(str, enum.Enum):
    libre   = "libre"
    occupee = "occupee"


class Chambre(Base):
    __tablename__ = "chambres"

    id          = Column(Integer, primary_key=True, index=True)
    cite_id     = Column(Integer, ForeignKey("cites.id", ondelete="CASCADE"), nullable=False)
    nom         = Column(String(50), nullable=False)
    description = Column(String(500), default="")
    equipee     = Column(Boolean, default=False)
    prix        = Column(Float, default=0.0)
    niveau      = Column(Integer, default=0)  # 0 = sous-sol
    etat        = Column(Enum(EtatChambre), default=EtatChambre.libre, nullable=False)
    localisation= Column(String(100), default="")
    image_path  = Column(String(300), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    cite      = relationship("Cite", back_populates="chambres")
    locataire = relationship("Locataire", back_populates="chambre", uselist=False)

    def __repr__(self):
        return f"<Chambre id={self.id} nom={self.nom} etat={self.etat}>"
