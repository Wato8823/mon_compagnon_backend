from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_responsable
from app.models.annonce import Annonce
from app.models.cite import Cite
from app.models.locataire import Locataire
from app.models.user import User
from app.schemas.annonce import AnnonceCreate, AnnonceUpdate, AnnonceResponse
from app.services.notification_service import notifier_tous_locataires_cite
from app.models.notification import NotifType

router = APIRouter(tags=["Annonces"])


def _check_cite_responsable(cite_id: int, user: User, db: Session) -> Cite:
    cite = db.query(Cite).filter(
        Cite.id == cite_id, Cite.responsable_id == user.id
    ).first()
    if not cite:
        raise HTTPException(status_code=404, detail="Cité introuvable ou accès refusé")
    return cite


# ── GET /cites/{cite_id}/annonces ────────────────────────────
@router.get("/cites/{cite_id}/annonces", response_model=List[AnnonceResponse])
def list_annonces(
    cite_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Liste toutes les annonces d'une cité (triées par date desc)."""
    cite = db.query(Cite).filter(Cite.id == cite_id).first()
    if not cite:
        raise HTTPException(status_code=404, detail="Cité introuvable")

    annonces = (
        db.query(Annonce)
        .filter(Annonce.cite_id == cite_id)
        .order_by(Annonce.date_publication.desc())
        .all()
    )
    return [AnnonceResponse.from_orm(a) for a in annonces]


# ── GET /annonces/mes-annonces ────────────────────────────────
@router.get("/annonces/mes-annonces", response_model=List[AnnonceResponse])
def mes_annonces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retourne les annonces visibles par le locataire connecté
    (celles de sa cité de résidence).
    """
    # Trouver la cité du locataire
    loc = (
        db.query(Locataire)
        .filter(Locataire.user_id == current_user.id, Locataire.actif == True)
        .first()
    )
    if not loc:
        return []

    annonces = (
        db.query(Annonce)
        .filter(Annonce.cite_id == loc.cite_id)
        .order_by(Annonce.date_publication.desc())
        .all()
    )
    return [AnnonceResponse.from_orm(a) for a in annonces]


# ── GET /cites/{cite_id}/annonces/{annonce_id} ───────────────
@router.get("/cites/{cite_id}/annonces/{annonce_id}", response_model=AnnonceResponse)
def get_annonce(
    cite_id: int,
    annonce_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    annonce = db.query(Annonce).filter(
        Annonce.id == annonce_id, Annonce.cite_id == cite_id
    ).first()
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce introuvable")
    return AnnonceResponse.from_orm(annonce)


# ── POST /cites/{cite_id}/annonces ───────────────────────────
@router.post("/cites/{cite_id}/annonces", response_model=AnnonceResponse, status_code=201)
def create_annonce(
    cite_id: int,
    payload: AnnonceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    """Publie une annonce et notifie tous les locataires de la cité."""
    _check_cite_responsable(cite_id, current_user, db)

    annonce = Annonce(
        cite_id=cite_id,
        auteur_id=current_user.id,
        titre=payload.titre,
        contenu=payload.contenu,
        important=payload.important,
        destinataires=payload.destinataires,
    )
    db.add(annonce)
    db.commit()
    db.refresh(annonce)

    # Notifier tous les locataires actifs de la cité
    notifier_tous_locataires_cite(
        db=db,
        cite_id=cite_id,
        titre=f"Nouvelle annonce : {payload.titre}",
        message=payload.contenu[:150] + ("..." if len(payload.contenu) > 150 else ""),
        type_notif=NotifType.annonce,
        ref_id=str(annonce.id),
    )

    return AnnonceResponse.from_orm(annonce)


# ── PUT /cites/{cite_id}/annonces/{annonce_id} ───────────────
@router.put("/cites/{cite_id}/annonces/{annonce_id}", response_model=AnnonceResponse)
def update_annonce(
    cite_id: int,
    annonce_id: int,
    payload: AnnonceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    _check_cite_responsable(cite_id, current_user, db)

    annonce = db.query(Annonce).filter(
        Annonce.id == annonce_id, Annonce.cite_id == cite_id
    ).first()
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce introuvable")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(annonce, field, value)

    db.commit()
    db.refresh(annonce)
    return AnnonceResponse.from_orm(annonce)


# ── DELETE /cites/{cite_id}/annonces/{annonce_id} ────────────
@router.delete("/cites/{cite_id}/annonces/{annonce_id}", status_code=204)
def delete_annonce(
    cite_id: int,
    annonce_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    _check_cite_responsable(cite_id, current_user, db)

    annonce = db.query(Annonce).filter(
        Annonce.id == annonce_id, Annonce.cite_id == cite_id
    ).first()
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce introuvable")

    db.delete(annonce)
    db.commit()
