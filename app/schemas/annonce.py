from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.notification import NotifType


# ════════════════════════════════════════════════════════════
#  ANNONCE
# ════════════════════════════════════════════════════════════

class AnnonceCreate(BaseModel):
    titre: str
    contenu: str
    important: bool = False
    destinataires: List[str] = ["tous"]


class AnnonceUpdate(BaseModel):
    titre: Optional[str] = None
    contenu: Optional[str] = None
    important: Optional[bool] = None
    destinataires: Optional[List[str]] = None


class AnnonceResponse(BaseModel):
    id: int
    titre: str
    contenu: str
    cite_id: int
    auteur_id: Optional[int] = None
    auteur_nom: str
    date_publication: datetime
    important: bool
    destinataires: List[str]

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            titre=obj.titre,
            contenu=obj.contenu,
            cite_id=obj.cite_id,
            auteur_id=obj.auteur_id,
            auteur_nom=obj.auteur_nom,
            date_publication=obj.date_publication,
            important=obj.important,
            destinataires=obj.destinataires or ["tous"],
        )


# ════════════════════════════════════════════════════════════
#  NOTIFICATION
# ════════════════════════════════════════════════════════════

class NotificationResponse(BaseModel):
    id: int
    titre: str
    message: str
    type: NotifType
    lue: bool
    ref_id: Optional[str] = None
    date: datetime

    model_config = {"from_attributes": True}


class NonLuesCountResponse(BaseModel):
    count: int
