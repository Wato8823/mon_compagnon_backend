from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Annonce(Base):
    __tablename__ = "annonces"

    id               = Column(Integer, primary_key=True, index=True)
    cite_id          = Column(Integer, ForeignKey("cites.id", ondelete="CASCADE"), nullable=False)
    auteur_id        = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    titre            = Column(String(200), nullable=False)
    contenu          = Column(String(2000), nullable=False)
    important        = Column(Boolean, default=False)
    destinataires    = Column(JSON, default=["tous"])  # ['tous'] ou liste d'IDs
    date_publication = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    cite   = relationship("Cite", back_populates="annonces")
    auteur = relationship("User", foreign_keys=[auteur_id])

    @property
    def auteur_nom(self) -> str:
        if self.auteur:
            return f"{self.auteur.nom} {self.auteur.prenom}"
        return "Responsable"

    def __repr__(self):
        return f"<Annonce id={self.id} titre={self.titre}>"
