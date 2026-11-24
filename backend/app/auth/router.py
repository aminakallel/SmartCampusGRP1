from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import UUID4

from app.api.routes.conversation_attachment import get_conversation_attachment_service
from app.auth.dependencies import get_current_user, get_jwt_settings, get_user_repository
from app.auth.models import UserAccount
from app.auth.postgres_repository import DatabaseUnavailable
from app.auth.repository import DuplicateEmail, UserRepository
from app.auth.schemas import AuthResponse, LoginRequest, PublicUser, RegisterRequest
from app.auth.security import JWTSettings, create_access_token
from app.auth.service import AuthService, InvalidCredentials
from app.services.conversation_attachment import (
    AttachmentError,
    ConversationAttachmentService,
    GuestContextAlreadyClaimed,
    GuestContextNotFound,
)


router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


def get_auth_service(
    repository: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(repository)


def _public_user(user: UserAccount) -> PublicUser:
    return PublicUser(
        id=user.id,
        nom=user.nom,
        prenom=user.prenom,
        email=user.email,
        role=user.role,
        langue_preferee=user.langue_preferee,
    )


def _try_attach_session(
    session_id: UUID4 | None,
    user: UserAccount,
    attachment_service: ConversationAttachmentService,
) -> bool:
    if session_id is None:
        return False
    try:
        attachment_service.attach(UUID(str(session_id)), user.id)
        return True
    except (GuestContextNotFound, GuestContextAlreadyClaimed, AttachmentError):
        # Account creation/login succeeds even if the visitor session is no
        # longer attachable; the response reports the failed attachment.
        return False


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
    settings: JWTSettings = Depends(get_jwt_settings),
    attachment_service: ConversationAttachmentService = Depends(
        get_conversation_attachment_service
    ),
) -> AuthResponse:
    try:
        user = auth_service.register_candidate(
            nom=data.nom,
            prenom=data.prenom,
            email=data.email,
            password=data.password,
            langue_preferee=data.langue_preferee,
        )
    except DuplicateEmail as exc:
        raise HTTPException(status_code=409, detail="An account already uses this email") from exc
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail="Account database is unavailable") from exc
    attached = _try_attach_session(data.session_id, user, attachment_service)
    return AuthResponse(
        access_token=create_access_token(user, settings),
        user=_public_user(user),
        conversation_rattachee=attached,
    )


@router.post("/login", response_model=AuthResponse)
def login(
    data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    settings: JWTSettings = Depends(get_jwt_settings),
    attachment_service: ConversationAttachmentService = Depends(
        get_conversation_attachment_service
    ),
) -> AuthResponse:
    try:
        user = auth_service.authenticate(data.email, data.password)
    except InvalidCredentials as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail="Account database is unavailable") from exc
    attached = _try_attach_session(data.session_id, user, attachment_service)
    return AuthResponse(
        access_token=create_access_token(user, settings),
        user=_public_user(user),
        conversation_rattachee=attached,
    )


@router.get("/me", response_model=PublicUser)
def me(user: UserAccount = Depends(get_current_user)) -> PublicUser:
    return _public_user(user)
