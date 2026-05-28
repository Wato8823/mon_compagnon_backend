# Mon Compagnon Backend FastAPI

API REST pour l'application mobile de gestion de citÃ©s universitaires.

---

## Stack technique

| Outil | Version | RÃ´le |
|-------|---------|------|
| Python | 3.11.9 | Langage |
| FastAPI | 0.111.0 | Framework web |
| SQLAlchemy | 2.0.30 | ORM |
| PostgreSQL | 14+ | Base de donnÃ©es |
| Alembic | 1.13.1 | Migrations |
| Pydantic | 2.7.1 | Validation |
| python-jose | 3.3.0 | JWT |
| passlib + bcrypt | 1.7.4 + 4.0.1 | Mots de passe |
| Cloudinary | 1.40.0 | Stockage images |
| APScheduler | 3.10.4 | TÃ¢ches planifiÃ©es |
| Uvicorn | 0.29.0 | Serveur ASGI |

---

## Installation locale (Windows)

### PrÃ©requis
- Python **3.11.9** (`python --version`)
- PostgreSQL 14+
- Git

### Ã‰tapes

```cmd
rem 1. Cloner / ouvrir le dossier
cd backend

rem 2. CrÃ©er l'environnement virtuel Python 3.11
python -m venv venv

rem 3. Activer
venv\Scripts\activate

rem 4. Mettre Ã  jour pip
python -m pip install --upgrade pip setuptools wheel

rem 5. Installer les dÃ©pendances
pip install -r requirements.txt

rem 6. Configurer l'environnement
copy .env.example .env
rem â†’ Ã‰diter .env avec tes valeurs

rem 7. CrÃ©er la base de donnÃ©es (via pgAdmin ou psql)
rem    CrÃ©er une base nommÃ©e : mon_compagnon

rem 8. Peupler avec les donnÃ©es de test
python -m app.utils.seed

rem 9. Lancer le serveur
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera accessible sur : http://localhost:8000
Documentation Swagger : http://localhost:8000/docs

---

## Variables d'environnement (.env)

```env
# Base de donnÃ©es
DATABASE_URL=postgresql://postgres:tonmdp@localhost:5432/mon_compagnon

# JWT â€” gÃ©nÃ©rer avec : python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=votre-cle-secrete-minimum-32-caracteres

# Cloudinary (crÃ©er compte gratuit sur cloudinary.com)
CLOUDINARY_CLOUD_NAME=votre_cloud_name
CLOUDINARY_API_KEY=votre_api_key
CLOUDINARY_API_SECRET=votre_api_secret

# Optionnel
DEBUG=true
BAIL_ALERTE_JOURS=30
```

---

## DÃ©ploiement sur Render

### Ã‰tape 1 â€” PostgreSQL sur Render

1. Va sur https://render.com â†’ **New** â†’ **PostgreSQL**
2. Nom : `mon-compagnon-db`
3. Plan : **Free**
4. Clique **Create Database**
5. Copie l'**Internal Database URL**

### Ã‰tape 2 â€” Cloudinary (stockage images gratuit)

1. Va sur https://cloudinary.com â†’ crÃ©er un compte gratuit
2. Dans le Dashboard, copie :
   - **Cloud Name**
   - **API Key**
   - **API Secret**

### Ã‰tape 3 â€” Web Service sur Render

1. **New** â†’ **Web Service**
2. Connecte ton repo GitHub (push le dossier `backend/` d'abord)
3. ParamÃ¨tres :
   ```
   Name      : mon-compagnon-api
   Runtime   : Python 3
   Build Cmd : pip install -r requirements.txt
   Start Cmd : uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. Onglet **Environment** â†’ ajouter les variables :

| ClÃ© | Valeur |
|-----|--------|
| `DATABASE_URL` | Internal URL depuis l'Ã©tape 1 |
| `SECRET_KEY` | ClÃ© gÃ©nÃ©rÃ©e (voir ci-dessous) |
| `CLOUDINARY_CLOUD_NAME` | Depuis Cloudinary |
| `CLOUDINARY_API_KEY` | Depuis Cloudinary |
| `CLOUDINARY_API_SECRET` | Depuis Cloudinary |
| `DEBUG` | `false` |
| `ALLOWED_ORIGINS` | `*` |

**Generer une SECRET_KEY :**
```python
python -c "import secrets; print(secrets.token_hex(32))"
```

5. Clique **Create Web Service**

### Ã‰tape 4: Seed initial sur Render

Apres le premier deploiement, dans l'onglet **Shell** de ton service Render :
```bash
python -m app.utils.seed
```

### Ã‰tape 5: Connecter le frontend Flutter

Dans `frontend/lib/services/api_client.dart` :
```dart
// Remplacer par ton URL Render
static const String _baseUrl = 'https://mon-compagnon-api.onrender.com/api/v1';
```

---

## Gestion des images

Les images des cites et chambres sont stockees sur **Cloudinary**.

### Endpoints avec image (multipart/form-data)

**Creer une cite avec image :**
```
POST /api/v1/cites
Content-Type: multipart/form-data

nom         = "La Citadelle"
description = "Description..."
lieu        = "PK 19"
localisation= "12233N, 3ZE"
image       = [fichier image]
```

**Creer sans image (JSON) :**
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

Mªme logique pour les chambres : `/api/v1/cites/{cite_id}/chambres`

### Contraintes images
- Formats : JPEG, PNG, WEBP
- Taille max : 5 Mo
- Redimensionnement auto : max 800x600px
- Compression auto : qualitÃ© 85%

---

## Comptes de test (aprÃ¨s seed)

| RÃ´le | Email | Mot de passe |
|------|-------|-------------|
| Responsable | linjouom9@gmail.com | password123 |
| Ã‰tudiant 1 | kamga.paul@gmail.com | password123 |
| Ã‰tudiant 2 | nkomo.sarah@gmail.com | password123 |
| Ã‰tudiant 3 | biya.eric@yahoo.fr | password123 |

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

## RÃ©solution des erreurs courantes

**`postgres://` vs `postgresql://`**
Render fournit les URLs avec `postgres://` â€” le code corrige automatiquement.

**`pydantic-core` build error**
Utiliser Python 3.11.9 (pas 3.13). Mettre Ã  jour pip :
```cmd
python -m pip install --upgrade pip setuptools wheel
```

**`psycopg2-binary` build error**
VÃ©rifier Python 3.11.9. Si persistant, remplacer dans requirements.txt par `pg8000==1.31.1`
et dans `.env` : `DATABASE_URL=postgresql+pg8000://...`

**Port dÃ©jÃ  utilisÃ©**
```cmd
netstat -ano | findstr :8000
taskkill /PID <pid> /F
```
