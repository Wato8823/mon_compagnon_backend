from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class RoleEnum(str, enum.Enum):
    etudiant = "etudiant"
    responsable = "responsable"


class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    nom        = Column(String(100), nullable=False)
    prenom     = Column(String(100), nullable=False, default="")
    email      = Column(String(255), unique=True, index=True, nullable=False)
    phone1     = Column(String(20), default="")
    phone2     = Column(String(20), default="")
    password   = Column(String(255), nullable=False)
    role       = Column(Enum(RoleEnum), default=RoleEnum.etudiant, nullable=False)
    actif      = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    cites              = relationship("Cite", back_populates="responsable", cascade="all, delete-orphan")
    notifications      = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    locataire_profile  = relationship("Locataire", back_populates="user", uselist=False)

    @property
    def has_cite(self) -> bool:
        return len(self.cites) > 0

    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.role}>"
