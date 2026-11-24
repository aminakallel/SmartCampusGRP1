from app.auth.models import UserAccount
from app.auth.repository import UserRepository
from app.auth.security import hash_password, verify_password


class InvalidCredentials(ValueError):
    """Credentials are invalid or the account is inactive."""


class AuthService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def register_candidate(
        self,
        *,
        nom: str,
        prenom: str,
        email: str,
        password: str,
        langue_preferee: str = "fr",
    ) -> UserAccount:
        return self.repository.create_candidate(
            nom=nom,
            prenom=prenom,
            email=email,
            mot_de_passe_hash=hash_password(password),
            langue_preferee=langue_preferee,
        )

    def authenticate(self, email: str, password: str) -> UserAccount:
        user = self.repository.find_by_email(email)
        if (
            user is None
            or not user.est_actif
            or not verify_password(password, user.mot_de_passe_hash)
        ):
            raise InvalidCredentials("Invalid email or password")
        updated = self.repository.record_login(user.id)
        if updated is None:
            raise InvalidCredentials("Invalid email or password")
        return updated
