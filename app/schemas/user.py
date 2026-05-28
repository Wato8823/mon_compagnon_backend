from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from app.models.user import RoleEnum


# ── Requêtes ──────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    nom: str
    prenom: str = ""
    email: EmailStr
    password: str
    role: RoleEnum = RoleEnum.etudiant

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError("Le mot de passe doit contenir au moins 6 caractères")
        return v

    @field_validator("nom")
    @classmethod
    def nom_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Le nom est requis")
        return v.strip()


class LoginRequest(BaseModel):
    username: str   # email ou nom d'utilisateur
    password: str


class UpdateProfileRequest(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    email: Optional[EmailStr] = None
    phone1: Optional[str] = None
    phone2: Optional[str] = None


# ── Réponses ──────────────────────────────────────────────────
class UserResponse(BaseModel):
    id: int
    nom: str
    prenom: str
    email: str
    phone1: str
    phone2: str
    role: RoleEnum
    has_cite: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_user(cls, user):
        return cls(
            id=user.id,
            nom=user.nom,
            prenom=user.prenom,
            email=user.email,
            phone1=user.phone1 or "",
            phone2=user.phone2 or "",
            role=user.role,
            has_cite=user.has_cite,
            created_at=user.created_at,
        )


class TokenResponse(BaseModel):
    token: str
    user: UserResponse
