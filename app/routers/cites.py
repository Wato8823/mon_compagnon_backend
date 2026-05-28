from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from fastapi import status as http_status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user, require_responsable
from app.models.cite import Cite
from app.models.chambre import Chambre, EtatChambre
from app.models.user import User
from app.schemas.cite import (
    CiteCreate, CiteUpdate, CiteResponse,
    ChambreCreate, ChambreUpdate, ChambreResponse,
)
from app.services.image_service import upload_image, delete_image
import json

router = APIRouter(tags=["Cités & Chambres"])


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

def _get_cite_owned(cite_id: int, user: User, db: Session) -> Cite:
    cite = db.query(Cite).filter(
        Cite.id == cite_id, Cite.responsable_id == user.id
    ).first()
    if not cite:
        raise HTTPException(
            status_code=404, detail="Cité introuvable ou accès refusé"
        )
    return cite


# ══════════════════════════════════════════════════════════════
#  CITÉS
# ══════════════════════════════════════════════════════════════

# ── GET /cites ────────────────────────────────────────────────
@router.get("/cites", response_model=List[CiteResponse])
def list_cites(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Liste toutes les cités disponibles."""
    cites = db.query(Cite).all()
    return [CiteResponse.from_orm(c) for c in cites]


# ── GET /cites/mes-cites ──────────────────────────────────────
@router.get("/cites/mes-cites", response_model=List[CiteResponse])
def mes_cites(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    """Cités du responsable connecté."""
    cites = db.query(Cite).filter(
        Cite.responsable_id == current_user.id
    ).all()
    return [CiteResponse.from_orm(c) for c in cites]


# ── GET /cites/{cite_id} ──────────────────────────────────────
@router.get("/cites/{cite_id}", response_model=CiteResponse)
def get_cite(
    cite_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cite = db.query(Cite).filter(Cite.id == cite_id).first()
    if not cite:
        raise HTTPException(status_code=404, detail="Cité introuvable")
    return CiteResponse.from_orm(cite)


# ── POST /cites ───────────────────────────────────────────────
@router.post("/cites", response_model=CiteResponse, status_code=201)
async def create_cite(
    nom: str = Form(...),
    description: str = Form(""),
    lieu: str = Form(""),
    localisation: str = Form(""),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    """
    Crée une nouvelle cité.
    Accepte un formulaire multipart avec image optionnelle.
    """
    # Upload image si fournie
    image_url = None
    if image and image.filename:
        image_url = upload_image(image, folder="cites")

    cite = Cite(
        nom=nom.strip(),
        description=description,
        lieu=lieu,
        localisation=localisation,
        image_path=image_url,
        responsable_id=current_user.id,
    )
    db.add(cite)
    db.commit()
    db.refresh(cite)
    return CiteResponse.from_orm(cite)


# ── POST /cites (JSON sans image) ────────────────────────────
@router.post("/cites/json", response_model=CiteResponse, status_code=201)
def create_cite_json(
    payload: CiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    """Crée une cité sans image (body JSON standard)."""
    cite = Cite(**payload.model_dump(), responsable_id=current_user.id)
    db.add(cite)
    db.commit()
    db.refresh(cite)
    return CiteResponse.from_orm(cite)


# ── PUT /cites/{cite_id} ──────────────────────────────────────
@router.put("/cites/{cite_id}", response_model=CiteResponse)
def update_cite(
    cite_id: int,
    payload: CiteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    """Modifie les infos textuelles d'une cité."""
    cite = _get_cite_owned(cite_id, current_user, db)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(cite, field, value)
    db.commit()
    db.refresh(cite)
    return CiteResponse.from_orm(cite)


# ── POST /cites/{cite_id}/image ───────────────────────────────
@router.post("/cites/{cite_id}/image", response_model=CiteResponse)
async def upload_cite_image(
    cite_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    """
    Upload ou remplace l'image d'une cité existante.
    Endpoint séparé pour pouvoir modifier l'image indépendamment.
    """
    cite = _get_cite_owned(cite_id, current_user, db)

    # Supprimer l'ancienne image Cloudinary
    if cite.image_path:
        delete_image(cite.image_path)

    # Uploader la nouvelle
    cite.image_path = upload_image(image, folder="cites")
    db.commit()
    db.refresh(cite)
    return CiteResponse.from_orm(cite)


# ── DELETE /cites/{cite_id}/image ─────────────────────────────
@router.delete("/cites/{cite_id}/image", response_model=CiteResponse)
def delete_cite_image(
    cite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    """Supprime l'image d'une cité."""
    cite = _get_cite_owned(cite_id, current_user, db)
    if cite.image_path:
        delete_image(cite.image_path)
        cite.image_path = None
        db.commit()
        db.refresh(cite)
    return CiteResponse.from_orm(cite)


# ── DELETE /cites/{cite_id} ───────────────────────────────────
@router.delete("/cites/{cite_id}", status_code=204)
def delete_cite(
    cite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    cite = _get_cite_owned(cite_id, current_user, db)
    # Supprimer l'image Cloudinary
    if cite.image_path:
        delete_image(cite.image_path)
    db.delete(cite)
    db.commit()


# ══════════════════════════════════════════════════════════════
#  CHAMBRES
# ══════════════════════════════════════════════════════════════

# ── GET /cites/{cite_id}/chambres ─────────────────────────────
@router.get("/cites/{cite_id}/chambres", response_model=List[ChambreResponse])
def list_chambres(
    cite_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cite = db.query(Cite).filter(Cite.id == cite_id).first()
    if not cite:
        raise HTTPException(status_code=404, detail="Cité introuvable")
    chambres = db.query(Chambre).filter(Chambre.cite_id == cite_id).all()
    return [ChambreResponse.from_orm(c) for c in chambres]


# ── GET /cites/{cite_id}/chambres/{chambre_id} ────────────────
@router.get("/cites/{cite_id}/chambres/{chambre_id}", response_model=ChambreResponse)
def get_chambre(
    cite_id: int,
    chambre_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    chambre = db.query(Chambre).filter(
        Chambre.id == chambre_id, Chambre.cite_id == cite_id
    ).first()
    if not chambre:
        raise HTTPException(status_code=404, detail="Chambre introuvable")
    return ChambreResponse.from_orm(chambre)


# ── POST /cites/{cite_id}/chambres ────────────────────────────
@router.post("/cites/{cite_id}/chambres", response_model=ChambreResponse, status_code=201)
async def create_chambre(
    cite_id: int,
    nom: str = Form(...),
    description: str = Form(""),
    equipee: bool = Form(False),
    prix: float = Form(0.0),
    niveau: int = Form(0),
    etat: EtatChambre = Form(EtatChambre.libre),
    localisation: str = Form(""),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    """
    Crée une chambre dans une cité.
    Accepte un formulaire multipart avec image optionnelle.
    """
    _get_cite_owned(cite_id, current_user, db)

    # Upload image si fournie
    image_url = None
    if image and image.filename:
        image_url = upload_image(image, folder=f"chambres/cite_{cite_id}")

    chambre = Chambre(
        cite_id=cite_id,
        nom=nom.strip(),
        description=description,
        equipee=equipee,
        prix=prix,
        niveau=niveau,
        etat=etat,
        localisation=localisation,
        image_path=image_url,
    )
    db.add(chambre)
    db.commit()
    db.refresh(chambre)
    return ChambreResponse.from_orm(chambre)


# ── POST /cites/{cite_id}/chambres/json ───────────────────────
@router.post("/cites/{cite_id}/chambres/json", response_model=ChambreResponse, status_code=201)
def create_chambre_json(
    cite_id: int,
    payload: ChambreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    """Crée une chambre sans image (body JSON standard)."""
    _get_cite_owned(cite_id, current_user, db)
    chambre = Chambre(**payload.model_dump(), cite_id=cite_id)
    db.add(chambre)
    db.commit()
    db.refresh(chambre)
    return ChambreResponse.from_orm(chambre)


# ── POST /cites/{cite_id}/chambres/{chambre_id}/image ─────────
@router.post(
    "/cites/{cite_id}/chambres/{chambre_id}/image",
    response_model=ChambreResponse,
)
async def upload_chambre_image(
    cite_id: int,
    chambre_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    """Upload ou remplace l'image d'une chambre."""
    _get_cite_owned(cite_id, current_user, db)
    chambre = db.query(Chambre).filter(
        Chambre.id == chambre_id, Chambre.cite_id == cite_id
    ).first()
    if not chambre:
        raise HTTPException(status_code=404, detail="Chambre introuvable")

    # Supprimer l'ancienne
    if chambre.image_path:
        delete_image(chambre.image_path)

    chambre.image_path = upload_image(
        image, folder=f"chambres/cite_{cite_id}"
    )
    db.commit()
    db.refresh(chambre)
    return ChambreResponse.from_orm(chambre)


# ── PUT /cites/{cite_id}/chambres/{chambre_id} ────────────────
@router.put("/cites/{cite_id}/chambres/{chambre_id}", response_model=ChambreResponse)
def update_chambre(
    cite_id: int,
    chambre_id: int,
    payload: ChambreUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    _get_cite_owned(cite_id, current_user, db)
    chambre = db.query(Chambre).filter(
        Chambre.id == chambre_id, Chambre.cite_id == cite_id
    ).first()
    if not chambre:
        raise HTTPException(status_code=404, detail="Chambre introuvable")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(chambre, field, value)
    db.commit()
    db.refresh(chambre)
    return ChambreResponse.from_orm(chambre)


# ── DELETE /cites/{cite_id}/chambres/{chambre_id}/image ───────
@router.delete(
    "/cites/{cite_id}/chambres/{chambre_id}/image",
    response_model=ChambreResponse,
)
def delete_chambre_image(
    cite_id: int,
    chambre_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    """Supprime l'image d'une chambre."""
    _get_cite_owned(cite_id, current_user, db)
    chambre = db.query(Chambre).filter(
        Chambre.id == chambre_id, Chambre.cite_id == cite_id
    ).first()
    if not chambre:
        raise HTTPException(status_code=404, detail="Chambre introuvable")
    if chambre.image_path:
        delete_image(chambre.image_path)
        chambre.image_path = None
        db.commit()
        db.refresh(chambre)
    return ChambreResponse.from_orm(chambre)


# ── DELETE /cites/{cite_id}/chambres/{chambre_id} ─────────────
@router.delete("/cites/{cite_id}/chambres/{chambre_id}", status_code=204)
def delete_chambre(
    cite_id: int,
    chambre_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_responsable),
):
    _get_cite_owned(cite_id, current_user, db)
    chambre = db.query(Chambre).filter(
        Chambre.id == chambre_id, Chambre.cite_id == cite_id
    ).first()
    if not chambre:
        raise HTTPException(status_code=404, detail="Chambre introuvable")
    if chambre.image_path:
        delete_image(chambre.image_path)
    db.delete(chambre)
    db.commit()
