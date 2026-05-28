from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user, require_responsable
from app.models.cite import Cite
from app.models.chambre import Chambre, EtatChambre
from app.models.locataire import Locataire
from app.models.user import User
from app.schemas.locataire import (
    LocataireCreate, LocataireUpdate,
    RenouvellerBailRequest, LocataireResponse,
)
from app.services.notification_service import creer_notification
from app.models.notification import NotifType

router = APIRouter(tags=["Locataires"])


def _check_cite_responsable(cite_id: int, user: User, db: Session) -> Cite:
    """Vérifie que la cité appartient au responsable connecté."""
    cite = db.query(Cite).filter(
        Cite.id == cite_id, Cite.responsable_id == user.id
    ).first()
    if not cite:
        raise HTTPException(status_code=404, detail="Cité introuvable ou accès refusé")
    return cite


# ── GET /cites/{cite_id}/locataires ──────────────────────────
@router.get("/cites/{cite_id}/locataires", response_model=List[LocataireResponse])
def list_locataires(
    cite_id: int,
    expiration: Optional[int] = Query(None, description="Filtrer les baux expirant dans N jours"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    """Liste tous les locataires d'une cité avec filtrage optionnel."""
    _check_cite_responsable(cite_id, current_user, db)

    query = db.query(Locataire).filter(Locataire.cite_id == cite_id)
    locataires = query.all()

    # Filtre sur les baux expirant bientôt si demandé
    if expiration is not None:
        locataires = [l for l in locataires if 0 <= l.jours_restants <= expiration]

    return [LocataireResponse.from_orm(l) for l in locataires]


# ── GET /locataires ───────────────────────────────────────────
@router.get("/locataires", response_model=List[LocataireResponse])
def mes_locataires(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    """Tous les locataires des cités du responsable connecté."""
    cites_ids = [
        c.id for c in db.query(Cite).filter(Cite.responsable_id == current_user.id).all()
    ]
    locataires = (
        db.query(Locataire)
        .filter(Locataire.cite_id.in_(cites_ids))
        .all()
    )
    return [LocataireResponse.from_orm(l) for l in locataires]


# ── GET /locataires/{id} ──────────────────────────────────────
@router.get("/locataires/{locataire_id}", response_model=LocataireResponse)
def get_locataire(
    locataire_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    loc = db.query(Locataire).filter(Locataire.id == locataire_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Locataire introuvable")

    # Vérifier que la cité appartient au responsable
    _check_cite_responsable(loc.cite_id, current_user, db)
    return LocataireResponse.from_orm(loc)


# ── POST /locataires ──────────────────────────────────────────
@router.post("/locataires", response_model=LocataireResponse, status_code=201)
def create_locataire(
    payload: LocataireCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    """Ajoute un locataire à une cité et marque la chambre comme occupée."""
    _check_cite_responsable(payload.cite_id, current_user, db)

    # Vérifier que la chambre existe et est libre
    if payload.chambre_id:
        chambre = db.query(Chambre).filter(
            Chambre.id == payload.chambre_id,
            Chambre.cite_id == payload.cite_id,
        ).first()
        if not chambre:
            raise HTTPException(status_code=404, detail="Chambre introuvable")
        if chambre.etat == EtatChambre.occupee:
            raise HTTPException(status_code=409, detail="Cette chambre est déjà occupée")

    locataire = Locataire(**payload.model_dump())
    db.add(locataire)

    # Marquer la chambre comme occupée
    if payload.chambre_id and chambre:
        chambre.etat = EtatChambre.occupee

    db.commit()
    db.refresh(locataire)

    # Notification de bienvenue si le locataire a un compte
    if locataire.user_id:
        creer_notification(
            db,
            locataire.user_id,
            "Bienvenue !",
            f"Votre occupation de la chambre {locataire.chambre_nom} a été enregistrée.",
            NotifType.info,
            ref_id=str(locataire.id),
        )

    return LocataireResponse.from_orm(locataire)


# ── PUT /locataires/{id} ──────────────────────────────────────
@router.put("/locataires/{locataire_id}", response_model=LocataireResponse)
def update_locataire(
    locataire_id: int,
    payload: LocataireUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    loc = db.query(Locataire).filter(Locataire.id == locataire_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Locataire introuvable")

    _check_cite_responsable(loc.cite_id, current_user, db)

    # Si changement de chambre
    if payload.chambre_id and payload.chambre_id != loc.chambre_id:
        nouvelle_chambre = db.query(Chambre).filter(
            Chambre.id == payload.chambre_id
        ).first()
        if not nouvelle_chambre:
            raise HTTPException(status_code=404, detail="Nouvelle chambre introuvable")
        if nouvelle_chambre.etat == EtatChambre.occupee:
            raise HTTPException(status_code=409, detail="Cette chambre est déjà occupée")

        # Libérer l'ancienne chambre
        if loc.chambre_id:
            ancienne = db.query(Chambre).filter(Chambre.id == loc.chambre_id).first()
            if ancienne:
                ancienne.etat = EtatChambre.libre

        # Occuper la nouvelle chambre
        nouvelle_chambre.etat = EtatChambre.occupee

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(loc, field, value)

    db.commit()
    db.refresh(loc)
    return LocataireResponse.from_orm(loc)


# ── PUT /locataires/{id}/renouveler ──────────────────────────
@router.put("/locataires/{locataire_id}/renouveler", response_model=LocataireResponse)
def renouveler_bail(
    locataire_id: int,
    payload: RenouvellerBailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    """Renouvelle la date limite du bail d'un locataire."""
    loc = db.query(Locataire).filter(Locataire.id == locataire_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Locataire introuvable")

    _check_cite_responsable(loc.cite_id, current_user, db)

    if payload.date_limite <= loc.date_limite:
        raise HTTPException(
            status_code=400,
            detail="La nouvelle date doit être postérieure à la date actuelle"
        )

    loc.date_limite = payload.date_limite
    loc.actif = True
    db.commit()
    db.refresh(loc)

    # Notification au locataire
    if loc.user_id:
        date_str = payload.date_limite.strftime("%d/%m/%Y")
        creer_notification(
            db,
            loc.user_id,
            "Bail renouvelé",
            f"Votre bail pour la chambre {loc.chambre_nom} a été renouvelé "
            f"jusqu'au {date_str}.",
            NotifType.info,
            ref_id=str(loc.id),
        )

    return LocataireResponse.from_orm(loc)


# ── DELETE /locataires/{id} ───────────────────────────────────
@router.delete("/locataires/{locataire_id}", status_code=204)
def delete_locataire(
    locataire_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    """Résilie le bail d'un locataire et libère la chambre."""
    loc = db.query(Locataire).filter(Locataire.id == locataire_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Locataire introuvable")

    _check_cite_responsable(loc.cite_id, current_user, db)

    # Libérer la chambre
    if loc.chambre_id:
        chambre = db.query(Chambre).filter(Chambre.id == loc.chambre_id).first()
        if chambre:
            chambre.etat = EtatChambre.libre

    # Notifier le locataire
    if loc.user_id:
        creer_notification(
            db,
            loc.user_id,
            "Bail résilié",
            f"Votre bail pour la chambre {loc.chambre_nom} a été résilié.",
            NotifType.info,
            ref_id=str(loc.id),
        )

    db.delete(loc)
    db.commit()
