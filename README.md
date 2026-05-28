# Mon Compagnon — Backend FastAPI

API REST pour l'application mobile de gestion de cités universitaires.

---

## Stack technique

| Outil | Version | Rôle |
|-------|---------|------|
| Python | 3.11.9 | Langage |
| FastAPI | 0.111.0 | Framework web |
| SQLAlchemy | 2.0.30 | ORM |
| PostgreSQL | 14+ | Base de données |
| Alembic | 1.13.1 | Migrations |
| Pydantic | 2.7.1 | Validation |
| python-jose | 3.3.0 | JWT |
| passlib + bcrypt | 1.7.4 + 4.0.1 | Mots de passe |
| Cloudinary | 1.40.0 | Stockage images |
| APScheduler | 3.10.4 | Tâches planifiées |
| Uvicorn | 0.29.0 | Serveur ASGI |

---

## Installation locale (Windows)

### Prérequis
- Python **3.11.9** (`python --version`)
- PostgreSQL 14+
- Git

### Étapes

```cmd
rem 1. Cloner / ouvrir le dossier
cd backend

rem 2. Créer l'environnement virtuel Python 3.11
python -m venv venv

rem 3. Activer
venv\Scripts\activate

rem 4. Mettre à jour pip
python -m pip install --upgrade pip setuptools wheel

rem 5. Installer les dépendances
pip install -r requirements.txt

rem 6. Configurer l'environnement
copy .env.example .env
rem → Éditer .env avec tes valeurs

rem 7. Créer la base de données (via pgAdmin ou psql)
rem    Créer une base nommée : mon_compagnon

rem 8. Peupler avec les données de test
python -m app.utils.seed

rem 9. Lancer le serveur
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

L'API est accessible sur : http://localhost:8000
Documentation Swagger : http://localhost:8000/docs

---

## Variables d'environnement (.env)

```env
# Base de données
DATABASE_URL=postgresql://postgres:tonmdp@localhost:5432/mon_compagnon

# JWT — générer avec : python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=votre-cle-secrete-minimum-32-caracteres

# Cloudinary (créer compte gratuit sur cloudinary.com)
CLOUDINARY_CLOUD_NAME=votre_cloud_name
CLOUDINARY_API_KEY=votre_api_key
CLOUDINARY_API_SECRET=votre_api_secret

# Optionnel
DEBUG=true
BAIL_ALERTE_JOURS=30
```

---

## Déploiement sur Render

### Étape 1 — PostgreSQL sur Render

1. Va sur https://render.com → **New** → **PostgreSQL**
2. Nom : `mon-compagnon-db`
3. Plan : **Free**
4. Clique **Create Database**
5. Copie l'**Internal Database URL**

### Étape 2 — Cloudinary (stockage images gratuit)

1. Va sur https://cloudinary.com → créer un compte gratuit
2. Dans le Dashboard, copie :
   - **Cloud Name**
   - **API Key**
   - **API Secret**

### Étape 3 — Web Service sur Render

1. **New** → **Web Service**
2. Connecte ton repo GitHub (push le dossier `backend/` d'abord)
3. Paramètres :
   ```
   Name      : mon-compagnon-api
   Runtime   : Python 3
   Build Cmd : pip install -r requirements.txt
   Start Cmd : uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. Onglet **Environment** → ajouter les variables :

| Clé | Valeur |
|-----|--------|
| `DATABASE_URL` | Internal URL depuis l'étape 1 |
| `SECRET_KEY` | Clé générée (voir ci-dessous) |
| `CLOUDINARY_CLOUD_NAME` | Depuis Cloudinary |
| `CLOUDINARY_API_KEY` | Depuis Cloudinary |
| `CLOUDINARY_API_SECRET` | Depuis Cloudinary |
| `DEBUG` | `false` |
| `ALLOWED_ORIGINS` | `*` |

**Générer une SECRET_KEY :**
```python
python -c "import secrets; print(secrets.token_hex(32))"
```

5. Clique **Create Web Service**

### Étape 4 — Seed initial sur Render

Après le premier déploiement, dans l'onglet **Shell** de ton service Render :
```bash
python -m app.utils.seed
```

### Étape 5 — Connecter le frontend Flutter

Dans `frontend/lib/services/api_client.dart` :
```dart
// Remplacer par ton URL Render
static const String _baseUrl = 'https://mon-compagnon-api.onrender.com/api/v1';
```

---

## Gestion des images

Les images des cités et chambres sont stockées sur **Cloudinary**.

### Endpoints avec image (multipart/form-data)

**Créer une cité avec image :**
```
POST /api/v1/cites
Content-Type: multipart/form-data

nom         = "La Citadelle"
description = "Description..."
lieu        = "PK 19"
localisation= "12233N, 3ZE"
image       = [fichier image]
```

**Créer sans image (JSON) :**
```
POST /api/v1/cites/json
Content-Type: application/json

{"nom": "La Citadelle", "description": "...", "lieu": "PK19", "localisation": "..."}
```

**Ajouter/remplacer une image :**
```
POST /api/v1/cites/{id}/image
Content-Type: multipart/form-data
image = [fichier image]
```

**Supprimer l'image :**
```
DELETE /api/v1/cites/{id}/image
```

M�me logique pour les chambres : `/api/v1/cites/{cite_id}/chambres`

### Contraintes images
- Formats : JPEG, PNG, WEBP
- Taille max : 5 Mo
- Redimensionnement auto : max 800x600px
- Compression auto : qualité 85%

---

## Comptes de test (après seed)

| Rôle | Email | Mot de passe |
|------|-------|-------------|
| Responsable | linjouom9@gmail.com | password123 |
| Étudiant 1 | kamga.paul@gmail.com | password123 |
| Étudiant 2 | nkomo.sarah@gmail.com | password123 |
| Étudiant 3 | biya.eric@yahoo.fr | password123 |

---

## Tests

```cmd
rem Installer pytest
pip install pytest pytest-cov httpx

rem Lancer les tests
pytest tests/ -v

rem Avec couverture
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## Résolution des erreurs courantes

**`postgres://` vs `postgresql://`**
Render fournit les URLs avec `postgres://` — le code corrige automatiquement.

**`pydantic-core` build error**
Utiliser Python 3.11.9 (pas 3.13). Mettre à jour pip :
```cmd
python -m pip install --upgrade pip setuptools wheel
```

**`psycopg2-binary` build error**
Vérifier Python 3.11.9. Si persistant, remplacer dans requirements.txt par `pg8000==1.31.1`
et dans `.env` : `DATABASE_URL=postgresql+pg8000://...`

**Port déjà utilisé**
```cmd
netstat -ano | findstr :8000
taskkill /PID <pid> /F
```
