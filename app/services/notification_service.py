from sqlalchemy.orm import Session
from datetime import datetime
from app.models.locataire import Locataire
from app.models.notification import Notification, NotifType
from app.models.user import User
from app.core.config import settings


def creer_notification(
    db: Session,
    user_id: int,
    titre: str,
    message: str,
    type_notif: NotifType,
    ref_id: str = None,
) -> Notification:
    """Crée et sauvegarde une notification pour un utilisateur."""
    notif = Notification(
        user_id=user_id,
        titre=titre,
        message=message,
        type=type_notif,
        ref_id=ref_id,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def notifier_tous_locataires_cite(
    db: Session,
    cite_id: int,
    titre: str,
    message: str,
    type_notif: NotifType,
    ref_id: str = None,
):
    """Envoie une notification à tous les locataires actifs d'une cité."""
    locataires = (
        db.query(Locataire)
        .filter(Locataire.cite_id == cite_id, Locataire.actif == True)
        .all()
    )
    for loc in locataires:
        if loc.user_id:
            creer_notification(db, loc.user_id, titre, message, type_notif, ref_id)


def verifier_baux_expiration(db: Session):
    """
    Vérifie tous les locataires actifs dont le bail expire bientôt
    et crée des notifications si pas encore faites aujourd'hui.
    Appelé au démarrage et périodiquement par le scheduler.
    """
    seuil = settings.BAIL_ALERTE_JOURS
    locataires = (
        db.query(Locataire)
        .filter(Locataire.actif == True)
        .all()
    )

    for loc in locataires:
        jours = loc.jours_restants

        # Bail expiré — notifier
        if loc.est_expire and loc.user_id:
            # Vérifier si une notif d'expiration a déjà été envoyée aujourd'hui
            existante = (
                db.query(Notification)
                .filter(
                    Notification.user_id == loc.user_id,
                    Notification.type == NotifType.bailExpire,
                    Notification.ref_id == str(loc.id),
                )
                .order_by(Notification.date.desc())
                .first()
            )
            if not existante or (datetime.now() - existante.date).days >= 7:
                creer_notification(
                    db,
                    loc.user_id,
                    "Bail expiré",
                    f"Votre bail pour la chambre {loc.chambre_nom} a expiré. "
                    f"Veuillez contacter votre responsable.",
                    NotifType.bailExpire,
                    ref_id=str(loc.id),
                )

        # Bail expire bientôt — notifier une seule fois
        elif loc.expire_bientot and loc.user_id:
            existante = (
                db.query(Notification)
                .filter(
                    Notification.user_id == loc.user_id,
                    Notification.type == NotifType.bailBientotExpire,
                    Notification.ref_id == str(loc.id),
                )
                .first()
            )
            if not existante:
                date_str = loc.date_limite.strftime("%d/%m/%Y")
                creer_notification(
                    db,
                    loc.user_id,
                    "Bail bientôt expiré",
                    f"Votre bail pour la chambre {loc.chambre_nom} expire dans "
                    f"{jours} jour{'s' if jours > 1 else ''} ({date_str}). "
                    f"Pensez à renouveler.",
                    NotifType.bailBientotExpire,
                    ref_id=str(loc.id),
                )

        # Notifier aussi le responsable
        cite = loc.cite
        if cite and cite.responsable_id and loc.expire_bientot:
            existante_resp = (
                db.query(Notification)
                .filter(
                    Notification.user_id == cite.responsable_id,
                    Notification.type == NotifType.bailBientotExpire,
                    Notification.ref_id == f"resp_{loc.id}",
                )
                .first()
            )
            if not existante_resp:
                creer_notification(
                    db,
                    cite.responsable_id,
                    "Bail locataire bientôt expiré",
                    f"Le bail de {loc.nom} {loc.prenom} (chambre {loc.chambre_nom}) "
                    f"expire dans {jours} jour{'s' if jours > 1 else ''}.",
                    NotifType.bailBientotExpire,
                    ref_id=f"resp_{loc.id}",
                )
