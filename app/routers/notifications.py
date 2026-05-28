from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.notification import Notification
from app.models.user import User
from app.schemas.annonce import NotificationResponse, NonLuesCountResponse
from app.services.notification_service import verifier_baux_expiration

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# ── GET /notifications ────────────────────────────────────────
@router.get("", response_model=List[NotificationResponse])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Liste toutes les notifications de l'utilisateur connecté (les plus récentes en premier)."""
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.date.desc())
        .all()
    )


# ── GET /notifications/non-lues/count ────────────────────────
@router.get("/non-lues/count", response_model=NonLuesCountResponse)
def count_non_lues(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne le nombre de notifications non lues."""
    count = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.lue == False,
        )
        .count()
    )
    return NonLuesCountResponse(count=count)


# ── PUT /notifications/tout-lire ──────────────────────────────
@router.put("/tout-lire")
def marquer_toutes_lues(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Marque toutes les notifications de l'utilisateur comme lues."""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.lue == False,
    ).update({"lue": True})
    db.commit()
    return {"message": "Toutes les notifications ont été marquées comme lues"}


# ── PUT /notifications/{id}/lue ───────────────────────────────
@router.put("/{notif_id}/lue", response_model=NotificationResponse)
def marquer_lue(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Marque une notification spécifique comme lue."""
    notif = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == current_user.id,
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification introuvable")

    notif.lue = True
    db.commit()
    db.refresh(notif)
    return notif


# ── DELETE /notifications/{id} ───────────────────────────────
@router.delete("/{notif_id}", status_code=204)
def delete_notification(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Supprime une notification."""
    notif = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == current_user.id,
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification introuvable")

    db.delete(notif)
    db.commit()


# ── POST /notifications/verifier-baux ────────────────────────
@router.post("/verifier-baux")
def verifier_baux(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Déclenche manuellement la vérification des baux expirant
    et crée les notifications nécessaires.
    Appelé par le frontend au démarrage de l'app.
    """
    verifier_baux_expiration(db)
    return {"message": "Vérification des baux effectuée"}
