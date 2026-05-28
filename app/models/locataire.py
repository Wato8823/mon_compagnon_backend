from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from app.core.database import Base


class Locataire(Base):
    __tablename__ = "locataires"

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    cite_id          = Column(Integer, ForeignKey("cites.id", ondelete="CASCADE"), nullable=False)
    chambre_id       = Column(Integer, ForeignKey("chambres.id", ondelete="SET NULL"), nullable=True)
    nom              = Column(String(100), nullable=False)
    prenom           = Column(String(100), nullable=False)
    email            = Column(String(255), nullable=False)
    telephone        = Column(String(20), default="")
    debut_occupation = Column(DateTime(timezone=True), nullable=False)
    date_limite      = Column(DateTime(timezone=True), nullable=False)
    actif            = Column(Boolean, default=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    user    = relationship("User", back_populates="locataire_profile")
    cite    = relationship("Cite", back_populates="locataires")
    chambre = relationship("Chambre", back_populates="locataire")

    @property
    def chambre_nom(self) -> str:
        return self.chambre.nom if self.chambre else ""

    @property
    def jours_restants(self) -> int:
        return (self.date_limite - datetime.now()).days

    @property
    def est_expire(self) -> bool:
        return self.jours_restants < 0

    @property
    def expire_bientot(self) -> bool:
        return 0 <= self.jours_restants <= 30

    def __repr__(self):
        return f"<Locataire id={self.id} nom={self.nom} {self.prenom}>"
