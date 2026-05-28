"""
Service de gestion des images via Cloudinary.
Cloudinary offre 25 GB de stockage gratuit — parfait pour Render.
"""
import cloudinary
import cloudinary.uploader
import cloudinary.api
from fastapi import UploadFile, HTTPException
from PIL import Image
import io
import uuid
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Configuration Cloudinary ──────────────────────────────────
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)

# ── Constantes ────────────────────────────────────────────────
MAX_FILE_SIZE_MB   = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_TYPES      = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
MAX_DIMENSION      = 2048   # px max largeur/hauteur
QUALITY            = 85     # compression JPEG


def _validate_image(file: UploadFile) -> bytes:
    """Valide le type et la taille du fichier uploadé."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté : {file.content_type}. "
                   f"Formats acceptés : JPEG, PNG, WEBP",
        )
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Fichier trop volumineux. Maximum : {MAX_FILE_SIZE_MB} Mo",
        )
    return content


def _optimize_image(content: bytes) -> bytes:
    """
    Optimise l'image : redimensionne si nécessaire et compresse.
    Retourne les bytes de l'image optimisée.
    """
    try:
        img = Image.open(io.BytesIO(content))

        # Convertir RGBA → RGB si nécessaire (PNG avec transparence)
        if img.mode in ("RGBA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)
            img = background

        # Redimensionner si trop grande
        w, h = img.size
        if w > MAX_DIMENSION or h > MAX_DIMENSION:
            ratio = min(MAX_DIMENSION / w, MAX_DIMENSION / h)
            new_size = (int(w * ratio), int(h * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            logger.info(f"Image redimensionnée : {w}x{h} → {new_size[0]}x{new_size[1]}")

        # Sauvegarder en JPEG optimisé
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=QUALITY, optimize=True)
        return buffer.getvalue()

    except Exception as e:
        logger.error(f"Erreur optimisation image : {e}")
        raise HTTPException(status_code=400, detail="Fichier image invalide ou corrompu")


def upload_image(file: UploadFile, folder: str = "mon_compagnon") -> str:
    """
    Upload une image sur Cloudinary et retourne l'URL publique.

    Args:
        file   : fichier UploadFile de FastAPI
        folder : dossier Cloudinary (ex: 'cites', 'chambres')

    Returns:
        URL publique de l'image
    """
    if not settings.CLOUDINARY_CLOUD_NAME:
        raise HTTPException(
            status_code=500,
            detail="Service d'images non configuré. "
                   "Vérifiez les variables CLOUDINARY_*",
        )

    # Validation
    content = _validate_image(file)

    # Optimisation
    optimized = _optimize_image(content)

    # Nom unique
    public_id = f"{folder}/{uuid.uuid4().hex}"

    try:
        result = cloudinary.uploader.upload(
            optimized,
            public_id=public_id,
            folder=folder,
            resource_type="image",
            overwrite=True,
            transformation=[
                {"width": 800, "height": 600, "crop": "limit"},
                {"quality": "auto:good"},
                {"fetch_format": "auto"},
            ],
        )
        url = result.get("secure_url", "")
        logger.info(f"Image uploadée : {url}")
        return url

    except Exception as e:
        logger.error(f"Erreur upload Cloudinary : {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'upload de l'image. Réessayez.",
        )


def delete_image(image_url: str) -> bool:
    """
    Supprime une image Cloudinary à partir de son URL.
    Retourne True si supprimée, False sinon.
    """
    if not image_url or not settings.CLOUDINARY_CLOUD_NAME:
        return False
    try:
        # Extraire le public_id depuis l'URL
        # URL : https://res.cloudinary.com/cloud/image/upload/v123/folder/id.jpg
        parts = image_url.split("/upload/")
        if len(parts) < 2:
            return False
        public_id_with_ext = parts[1]
        # Supprimer la version si présente (v1234567/)
        if public_id_with_ext.startswith("v"):
            public_id_with_ext = "/".join(public_id_with_ext.split("/")[1:])
        # Supprimer l'extension
        public_id = public_id_with_ext.rsplit(".", 1)[0]

        result = cloudinary.uploader.destroy(public_id)
        success = result.get("result") == "ok"
        if success:
            logger.info(f"Image supprimée : {public_id}")
        return success

    except Exception as e:
        logger.warning(f"Impossible de supprimer l'image {image_url} : {e}")
        return False


def is_cloudinary_configured() -> bool:
    """Vérifie si Cloudinary est correctement configuré."""
    return bool(
        settings.CLOUDINARY_CLOUD_NAME
        and settings.CLOUDINARY_API_KEY
        and settings.CLOUDINARY_API_SECRET
    )
