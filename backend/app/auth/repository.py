from dataclasses import replace
from datetime import datetime, timezone
from threading import RLock
from typing import Protocol
from uuid import UUID, uuid4

from app.auth.models import UserAccount, UserRole


class DuplicateEmail(ValueError):
    """An account already uses this normalized email address."""


class UserRepository(Protocol):
    def create_candidate(self, *, nom: str, prenom: str, email: str,
                         mot_de_passe_hash: str, langue_preferee: str = "fr") -> UserAccount: ...

    def find_by_email(self, email: str) -> UserAccount | None: ...

    def get_by_id(self, user_id: UUID) -> UserAccount | None: ...

    def record_login(self, user_id: UUID) -> UserAccount | None: ...


class InMemoryUserRepository:
    """Process-local account repository matching the SA-13 user table."""

    def __init__(self):
        self._by_id: dict[UUID, UserAccount] = {}
        self._id_by_email: dict[str, UUID] = {}
        self._lock = RLock()

    def create_candidate(
        self,
        *,
        nom: str,
        prenom: str,
        email: str,
        mot_de_passe_hash: str,
        langue_preferee: str = "fr",
    ) -> UserAccount:
        normalized_email = email.strip().lower()
        now = datetime.now(timezone.utc)
        user = UserAccount(
            id=uuid4(),
            nom=nom,
            prenom=prenom,
            email=normalized_email,
            mot_de_passe_hash=mot_de_passe_hash,
            role=UserRole.CANDIDAT,
            langue_preferee=langue_preferee,
            est_actif=True,
            derniere_connexion=None,
            cree_le=now,
            modifie_le=now,
        )
        return self.add(user)

    def add(self, user: UserAccount) -> UserAccount:
        """Insert a prepared account; used by trusted seed/admin provisioning only."""
        normalized_email = user.email.strip().lower()
        with self._lock:
            if normalized_email in self._id_by_email:
                raise DuplicateEmail("An account already uses this email")
            if user.id in self._by_id:
                raise ValueError("User UUID already exists")
            stored = replace(user, email=normalized_email)
            self._by_id[stored.id] = stored
            self._id_by_email[normalized_email] = stored.id
            return stored

    def find_by_email(self, email: str) -> UserAccount | None:
        with self._lock:
            user_id = self._id_by_email.get(email.strip().lower())
            return self._by_id.get(user_id) if user_id is not None else None

    def get_by_id(self, user_id: UUID) -> UserAccount | None:
        with self._lock:
            return self._by_id.get(user_id)

    def record_login(self, user_id: UUID) -> UserAccount | None:
        now = datetime.now(timezone.utc)
        with self._lock:
            user = self._by_id.get(user_id)
            if user is None:
                return None
            updated = replace(user, derniere_connexion=now, modifie_le=now)
            self._by_id[user_id] = updated
            return updated

    def delete(self, user_id: UUID) -> bool:
        """Remove an account created during a failed in-memory registration flow."""
        with self._lock:
            user = self._by_id.pop(user_id, None)
            if user is None:
                return False
            self._id_by_email.pop(user.email, None)
            return True

    def clear(self) -> None:
        with self._lock:
            self._by_id.clear()
            self._id_by_email.clear()
