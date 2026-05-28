from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.database import SessionLocal
from app.services.notification_service import verifier_baux_expiration
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="Africa/Douala")


def job_verifier_baux():
    """
    Tâche planifiée : vérifie chaque jour à 8h00
    si des baux expirent dans <= 30 jours et crée des notifications.
    """
    logger.info("⏰ [SCHEDULER] Vérification des baux en cours...")
    db = SessionLocal()
    try:
        verifier_baux_expiration(db)
        logger.info("✅ [SCHEDULER] Vérification des baux terminée.")
    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Erreur lors de la vérification des baux : {e}")
    finally:
        db.close()


def start_scheduler():
    """Démarre le scheduler avec la tâche quotidienne."""
    scheduler.add_job(
        job_verifier_baux,
        trigger=CronTrigger(hour=8, minute=0),   # Chaque jour à 08:00
        id="verifier_baux",
        name="Vérification baux expiration",
        replace_existing=True,
        misfire_grace_time=3600,  # Tolérance 1h si le serveur était off
    )
    scheduler.start()
    logger.info("🚀 Scheduler démarré — vérification baux tous les jours à 08h00")


def stop_scheduler():
    """Arrête proprement le scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("🛑 Scheduler arrêté.")
