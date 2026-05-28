from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from app.models.chambre import EtatChambre


# ════════════════════════════════════════════════════════════
#  CITÉ
# ════════════════════════════════════════════════════════════

class CiteCreate(BaseModel):
    nom: str
    description: str = ""
    lieu: str = ""
    localisation: str = ""

    @field_validator("nom")
    @classmethod
    def nom_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Le nom est requis")
        return v.strip()


class CiteUpdate(BaseModel):
    nom: Optional[str] = None
    description: Optional[str] = None
    lieu: Optional[str] = None
    localisation: Optional[str] = None
    note: Optional[float] = None


class CiteResponse(BaseModel):
    id: int
    nom: str
    description: str
    lieu: str
    localisation: str
    note: float
    image_path: Optional[str] = None
    image_url: Optional[str] = None   # URL complète Cloudinary
    responsable_id: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            nom=obj.nom,
            description=obj.description or "",
            lieu=obj.lieu or "",
            localisation=obj.localisation or "",
            note=obj.note or 5.0,
            image_path=obj.image_path,
            image_url=obj.image_path,   # image_path contient l'URL Cloudinary
            responsable_id=obj.responsable_id,
            created_at=obj.created_at,
        )


# ════════════════════════════════════════════════════════════
#  CHAMBRE
# ════════════════════════════════════════════════════════════

class ChambreCreate(BaseModel):
    nom: str
    description: str = ""
    equipee: bool = False
    prix: float = 0.0
    niveau: int = 0
    etat: EtatChambre = EtatChambre.libre
    localisation: str = ""

    @field_validator("nom")
    @classmethod
    def nom_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Le nom est requis")
        return v.strip()

    @field_validator("prix")
    @classmethod
    def prix_positif(cls, v):
        if v < 0:
            raise ValueError("Le prix doit être positif")
        return v


class ChambreUpdate(BaseModel):
    nom: Optional[str] = None
    description: Optional[str] = None
    equipee: Optional[bool] = None
    prix: Optional[float] = None
    niveau: Optional[int] = None
    etat: Optional[EtatChambre] = None
    localisation: Optional[str] = None


class ChambreResponse(BaseModel):
    id: int
    cite_id: int
    nom: str
    description: str
    equipee: bool
    prix: float
    niveau: int
    etat: EtatChambre
    localisation: str
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            cite_id=obj.cite_id,
            nom=obj.nom,
            description=obj.description or "",
            equipee=obj.equipee or False,
            prix=obj.prix or 0.0,
            niveau=obj.niveau or 0,
            etat=obj.etat,
            localisation=obj.localisation or "",
            image_path=obj.image_path,
            image_url=obj.image_path,
            created_at=obj.created_at,
        )
