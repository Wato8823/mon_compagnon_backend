from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class LocataireCreate(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    telephone: str = ""
    cite_id: int
    chambre_id: Optional[int] = None
    debut_occupation: datetime
    date_limite: datetime


class LocataireUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None
    chambre_id: Optional[int] = None
    debut_occupation: Optional[datetime] = None
    date_limite: Optional[datetime] = None
    actif: Optional[bool] = None


class RenouvellerBailRequest(BaseModel):
    date_limite: datetime


class LocataireResponse(BaseModel):
    id: int
    nom: str
    prenom: str
    email: str
    telephone: str
    cite_id: int
    chambre_id: Optional[int] = None
    chambre_nom: str
    debut_occupation: datetime
    date_limite: datetime
    actif: bool
    jours_restants: int
    est_expire: bool
    expire_bientot: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            nom=obj.nom,
            prenom=obj.prenom,
            email=obj.email,
            telephone=obj.telephone or "",
            cite_id=obj.cite_id,
            chambre_id=obj.chambre_id,
            chambre_nom=obj.chambre_nom,
            debut_occupation=obj.debut_occupation,
            date_limite=obj.date_limite,
            actif=obj.actif,
            jours_restants=obj.jours_restants,
            est_expire=obj.est_expire,
            expire_bientot=obj.expire_bientot,
            created_at=obj.created_at,
        )
