from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password, create_access_token, get_current_user
)
from app.models.user import User
from app.schemas.user import (
    RegisterRequest, LoginRequest, UpdateProfileRequest,
    UserResponse, TokenResponse
)

router = APIRouter(prefix="/auth", tags=["Authentification"])


# ── POST /auth/register ───────────────────────────────────────
@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Inscription d'un nouvel utilisateur."""
    # Vérifier email unique
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cet email est déjà utilisé"
        )

    user = User(
        nom=payload.nom,
        prenom=payload.prenom,
        email=payload.email,
        password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(token=token, user=UserResponse.from_orm_user(user))


# ── POST /auth/login ──────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Connexion par email ou nom d'utilisateur."""
    user = (
        db.query(User)
        .filter(
            (User.email == payload.username) | (User.nom == payload.username),
            User.actif == True,
        )
        .first()
    )

    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects"
        )

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(token=token, user=UserResponse.from_orm_user(user))


# ── POST /auth/logout ─────────────────────────────────────────
@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """
    Déconnexion — côté client, le token doit être supprimé.
    Côté serveur on confirme seulement (pas de blacklist de token ici).
    """
    return {"message": "Déconnexion réussie"}


# ── GET /auth/me ──────────────────────────────────────────────
@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    """Retourne le profil de l'utilisateur connecté."""
    return UserResponse.from_orm_user(current_user)


# ── PUT /auth/me ──────────────────────────────────────────────
@router.put("/me", response_model=UserResponse)
def update_profile(
    payload: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Modifie le profil de l'utilisateur connecté."""
    if payload.email and payload.email != current_user.email:
        if db.query(User).filter(User.email == payload.email).first():
            raise HTTPException(status_code=409, detail="Email déjà utilisé")

    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return UserResponse.from_orm_user(current_user)
