"""PostgreSQL implementation of the SA-13 `utilisateur` repository."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator
from uuid import UUID

import psycopg
from psycopg.errors import UniqueViolation
from psycopg.rows import dict_row

from app.auth.models import UserAccount, UserRole
from app.auth.repository import DuplicateEmail


class DatabaseUnavailable(RuntimeError):
    """The account database cannot currently be reached."""


class PostgresUserRepository:
    """Persists accounts in the SA-13 PostgreSQL `public.utilisateur` table."""

    def __init__(self, database_url: str):
        if not database_url.startswith(("postgresql://", "postgres://")):
            raise ValueError("DATABASE_URL must use PostgreSQL")
        self.database_url = database_url

    @contextmanager
    def _connection(self) -> Iterator[psycopg.Connection]:
        try:
            with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
                yield connection
        except psycopg.OperationalError as exc:
            raise DatabaseUnavailable("Account database is unavailable") from exc

    def create_candidate(
        self,
        *,
        nom: str,
        prenom: str,
        email: str,
        mot_de_passe_hash: str,
        langue_preferee: str = "fr",
    ) -> UserAccount:
        query = """
            INSERT INTO public.utilisateur
                (nom, prenom, email, mot_de_passe_hash, role, langue_preferee)
            VALUES (%s, %s, %s, %s, 'candidat', %s)
            RETURNING id, nom, prenom, email, mot_de_passe_hash, role,
                      langue_preferee, est_actif, derniere_connexion, cree_le, modifie_le
        """
        try:
            with self._connection() as connection:
                row = connection.execute(
                    query,
                    (nom, prenom, email.strip().lower(), mot_de_passe_hash, langue_preferee),
                ).fetchone()
        except UniqueViolation as exc:
            raise DuplicateEmail("An account already uses this email") from exc
        return self._to_user(row)

    def find_by_email(self, email: str) -> UserAccount | None:
        with self._connection() as connection:
            row = connection.execute(
                self._select_sql() + " WHERE lower(email) = lower(%s)",
                (email.strip(),),
            ).fetchone()
        return self._to_user(row) if row else None

    def get_by_id(self, user_id: UUID) -> UserAccount | None:
        with self._connection() as connection:
            row = connection.execute(
                self._select_sql() + " WHERE id = %s", (user_id,)
            ).fetchone()
        return self._to_user(row) if row else None

    def record_login(self, user_id: UUID) -> UserAccount | None:
        query = """
            UPDATE public.utilisateur
               SET derniere_connexion = now()
             WHERE id = %s
            RETURNING id, nom, prenom, email, mot_de_passe_hash, role,
                      langue_preferee, est_actif, derniere_connexion, cree_le, modifie_le
        """
        with self._connection() as connection:
            row = connection.execute(query, (user_id,)).fetchone()
        return self._to_user(row) if row else None

    def delete(self, user_id: UUID) -> bool:
        """Delete an account; mainly useful for controlled maintenance and tests."""
        with self._connection() as connection:
            result = connection.execute(
                "DELETE FROM public.utilisateur WHERE id = %s", (user_id,)
            )
        return result.rowcount > 0

    @staticmethod
    def _select_sql() -> str:
        return (
            "SELECT id, nom, prenom, email, mot_de_passe_hash, role, "
            "langue_preferee, est_actif, derniere_connexion, cree_le, modifie_le "
            "FROM public.utilisateur"
        )

    @staticmethod
    def _to_user(row: dict) -> UserAccount:
        return UserAccount(
            id=row["id"],
            nom=row["nom"],
            prenom=row["prenom"],
            email=row["email"],
            mot_de_passe_hash=row["mot_de_passe_hash"],
            role=UserRole(row["role"]),
            langue_preferee=row["langue_preferee"],
            est_actif=row["est_actif"],
            derniere_connexion=row["derniere_connexion"],
            cree_le=row["cree_le"],
            modifie_le=row["modifie_le"],
        )
