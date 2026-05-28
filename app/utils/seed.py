"""
Seed — Peuple la base de données avec des données de test.
Lancer avec : python -m app.utils.seed
"""
from datetime import datetime, timedelta
from app.core.database import SessionLocal, engine
from app.core.security import hash_password
from app.models import *   # Importe tous les modèles pour créer les tables


def seed():
    from app.core.database import Base
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Vérifier si des données existent déjà
        if db.query(User).count() > 0:
            print("⚠️  La base contient déjà des données. Seed annulé.")
            return

        print("🌱 Seeding de la base de données...")

        # ── Utilisateurs ──────────────────────────────────────
        responsable = User(
            nom="LINJOUOM",
            prenom="ALAIN PASCAL",
            email="linjouom9@gmail.com",
            password=hash_password("password123"),
            role="responsable",
            phone1="+237 694828353",
            phone2="+237 696855129",
        )
        etudiant1 = User(
            nom="KAMGA",
            prenom="Paul",
            email="kamga.paul@gmail.com",
            password=hash_password("password123"),
            role="etudiant",
            phone1="+237 677001122",
        )
        etudiant2 = User(
            nom="NKOMO",
            prenom="Sarah",
            email="nkomo.sarah@gmail.com",
            password=hash_password("password123"),
            role="etudiant",
            phone1="+237 699334455",
        )
        etudiant3 = User(
            nom="BIYA",
            prenom="Eric",
            email="biya.eric@yahoo.fr",
            password=hash_password("password123"),
            role="etudiant",
            phone1="+237 655778899",
        )
        db.add_all([responsable, etudiant1, etudiant2, etudiant3])
        db.flush()

        # ── Cités ─────────────────────────────────────────────
        cite1 = Cite(
            nom="La Citadelle",
            description="Cité dans barrières 5 étages, bien entretenue",
            lieu="PK 19",
            localisation="12233N, 3ZE",
            note=5.0,
            responsable_id=responsable.id,
        )
        cite2 = Cite(
            nom="Cité Khadafi",
            description="Grande résidence universitaire avec espaces communs",
            lieu="PK 19",
            localisation="12244N, 3ZF",
            note=4.5,
            responsable_id=responsable.id,
        )
        db.add_all([cite1, cite2])
        db.flush()

        # ── Chambres ──────────────────────────────────────────
        chambres_cite1 = [
            Chambre(cite_id=cite1.id, nom="Ch1", description="Chambre lumineuse niveau 1",
                    equipee=True, prix=25000, niveau=1, etat=EtatChambre.occupee),
            Chambre(cite_id=cite1.id, nom="Ch2", description="Chambre standard",
                    equipee=False, prix=20000, niveau=2, etat=EtatChambre.occupee),
            Chambre(cite_id=cite1.id, nom="Ch3", description="Chambre avec vue sur cour",
                    equipee=True, prix=30000, niveau=3, etat=EtatChambre.libre),
            Chambre(cite_id=cite1.id, nom="Ch4", description="Grande chambre équipée",
                    equipee=True, prix=35000, niveau=4, etat=EtatChambre.occupee),
            Chambre(cite_id=cite1.id, nom="Ch5", description="Chambre sous-sol ventilée",
                    equipee=True, prix=18000, niveau=0, etat=EtatChambre.libre),
            Chambre(cite_id=cite1.id, nom="Ch6", description="Chambre simple",
                    equipee=False, prix=15000, niveau=1, etat=EtatChambre.libre),
        ]
        db.add_all(chambres_cite1)
        db.flush()

        # ── Locataires ────────────────────────────────────────
        now = datetime.now()
        locataires = [
            Locataire(
                user_id=etudiant1.id, cite_id=cite1.id,
                chambre_id=chambres_cite1[0].id,
                nom="KAMGA", prenom="Paul",
                email="kamga.paul@gmail.com", telephone="+237 677001122",
                debut_occupation=datetime(2024, 1, 15),
                date_limite=now + timedelta(days=20),   # expire bientôt
                actif=True,
            ),
            Locataire(
                user_id=etudiant2.id, cite_id=cite1.id,
                chambre_id=chambres_cite1[1].id,
                nom="NKOMO", prenom="Sarah",
                email="nkomo.sarah@gmail.com", telephone="+237 699334455",
                debut_occupation=datetime(2024, 3, 1),
                date_limite=now + timedelta(days=90),   # bail en cours
                actif=True,
            ),
            Locataire(
                user_id=etudiant3.id, cite_id=cite1.id,
                chambre_id=chambres_cite1[3].id,
                nom="BIYA", prenom="Eric",
                email="biya.eric@yahoo.fr", telephone="+237 655778899",
                debut_occupation=datetime(2024, 6, 10),
                date_limite=now + timedelta(days=5),    # expire très bientôt
                actif=True,
            ),
        ]
        db.add_all(locataires)
        db.flush()

        # ── Annonces ──────────────────────────────────────────
        annonces = [
            Annonce(
                cite_id=cite1.id, auteur_id=responsable.id,
                titre="Coupure d'eau prévue",
                contenu="Une coupure d'eau est prévue le samedi 25 mai 2025 "
                        "de 8h à 14h pour travaux de maintenance.",
                important=True,
                destinataires=["tous"],
                date_publication=now - timedelta(hours=2),
            ),
            Annonce(
                cite_id=cite1.id, auteur_id=responsable.id,
                titre="Réunion des résidents",
                contenu="Une réunion de tous les résidents est organisée le vendredi "
                        "30 mai 2025 à 18h30 dans la salle commune.",
                important=False,
                destinataires=["tous"],
                date_publication=now - timedelta(days=1),
            ),
            Annonce(
                cite_id=cite1.id, auteur_id=responsable.id,
                titre="Rappel paiement mensuel",
                contenu="Rappel : le paiement du loyer du mois de mai est dû avant "
                        "le 5 juin. Passé ce délai, des pénalités seront appliquées.",
                important=False,
                destinataires=["tous"],
                date_publication=now - timedelta(days=3),
            ),
        ]
        db.add_all(annonces)
        db.commit()

        print("✅ Seed terminé avec succès !")
        print("\n📋 Comptes créés :")
        print(f"   👔 Responsable : linjouom9@gmail.com / password123")
        print(f"   👤 Étudiant 1  : kamga.paul@gmail.com / password123")
        print(f"   👤 Étudiant 2  : nkomo.sarah@gmail.com / password123")
        print(f"   👤 Étudiant 3  : biya.eric@yahoo.fr / password123")

    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors du seed : {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
