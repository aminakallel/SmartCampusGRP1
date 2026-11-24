# Backend — Sessions visiteur, mémoire et rattachement

Ce backend fournit une API minimale pour créer, lire et expirer une session visiteur sans compte. Il utilise actuellement un stockage simulé en mémoire, conformément au plan de travail si la base de données n’est pas prête.

## Contrat

- POST /api/v1/sessions/visiteur crée une session temporaire.
- GET /api/v1/sessions/visiteur lit la session fournie dans l’en-tête X-Session-ID.
- DELETE /api/v1/sessions/visiteur expire immédiatement la session fournie dans X-Session-ID.
- Les identifiants de session sont des UUID v4, conformément au modèle SA-13 et au contrat d’authentification visiteur SA-5.
- Le conversation_id suit provisoirement la forme conv_<UUID v4>, inspirée de l’exemple conv_102 du contrat SA-5 ; il reste ajustable après validation de l’équipe.
- La durée par défaut est de 24 heures ; elle peut être changée avec GUEST_SESSION_TTL_SECONDS.
- Les sessions inconnues ou expirées retournent une erreur 404 dans l’enveloppe d’erreur SA-5.

Le stockage en mémoire est local au processus : un redémarrage efface les sessions et plusieurs workers ne partagent pas le même état. Il sert de base de développement et doit être remplacé par PostgreSQL ou un cache partagé avant un déploiement multi-processus.

## Contrat commun SA-25 / SA-26 / SA-29

- SA-25 crée l'identifiant de session UUID v4, le `conversation_id` opaque et l'expiration (24 h par défaut).
- SA-26 est initialisée avec les mêmes `session_id`, `conversation_id` et `expires_at`. L'ajout d'un message ne crée pas de session arbitraire et ne prolonge pas son expiration. La mémoire conserve les 20 derniers messages.
- La suppression d'une session SA-25 supprime aussi la mémoire SA-26 associée.
- SA-29 expose `POST /api/v1/chat/rattacher`, avec `X-Session-ID` et Bearer. L'identifiant de compte vient de la dépendance d'authentification et ne peut pas être envoyé dans le corps.
- Les sessions invitées et la mémoire de conversation restent simulées en mémoire. Les comptes SA-28 sont persistés dans PostgreSQL par le dépôt SA-13; le rattachement SA-29 ne persiste pas encore dans `session_visiteur`.

Le stockage des messages est porté par SA-26; SA-25 reste propriétaire des identifiants et de l'expiration de la session.

## SA-28 — Authentification

- `POST /api/v1/auth/register` crée uniquement un compte candidat (`201`); un `session_id` UUID v4 est facultatif et peut être rattaché après l'inscription.
- `POST /api/v1/auth/login` vérifie l'email/mot de passe et émet un nouveau JWT; il accepte aussi un `session_id` facultatif pour le rattacher après connexion.
- `GET /api/v1/auth/me` renvoie l'utilisateur correspondant au Bearer token validé.
- Rôles SA-13 pris en charge : `candidat` et `admin`. L'inscription publique ne peut jamais attribuer le rôle admin.
- Les dépendances `require_candidate`, `require_admin` et `require_roles(...)` protègent les opérations selon le rôle courant lu depuis le dépôt.
- Les mots de passe sont hashés avec PBKDF2-HMAC-SHA256; seuls les hashes sont conservés. Les JWT HS256 contiennent `sub`, `email`, `role`, `iss`, `iat`, `exp` et `jti`.
- Les comptes utilisent `public.utilisateur` via `PostgresUserRepository`; `DATABASE_URL` est obligatoire. Le mode mémoire n'est disponible qu'en mettant explicitement `AUTH_USE_IN_MEMORY=true` pour les tests locaux; ne jamais l'activer en production.
- Le secret JWT n'a pas de valeur par défaut et les valeurs d'exemple sont refusées. Configurer `JWT_SECRET` avec une valeur aléatoire d'au moins 32 octets dans les secrets de déploiement, `JWT_ISSUER` (facultatif, défaut `smartcampus-api`) et `JWT_ACCESS_TOKEN_TTL_SECONDS` (facultatif, défaut 900, maximum 86400) avant d'utiliser `/auth`.

La gestion d'un administrateur doit être faite par un provisionnement contrôlé; aucune route publique ne permet de créer ou promouvoir un admin.

## Lancement local

Depuis le répertoire backend :

    python -m pip install -r requirements.txt
    # Générer une clé et l'enregistrer dans le gestionnaire de secrets du déploiement.
    python -c "import secrets; print(secrets.token_urlsafe(48))"
    # Appliquer backend/migrations/0001_users_profiles.sql sur la base PostgreSQL cible.
    # Définir DATABASE_URL et JWT_SECRET dans l'environnement, puis :
    uvicorn app.main:app

Pour le développement local avec un fichier `.env` ignoré par Git, démarrer avec `uvicorn app.main:app --env-file .env`. Ne jamais commiter ce fichier. En production, injecter `DATABASE_URL` et `JWT_SECRET` via le gestionnaire de secrets de la plateforme, avec un utilisateur SQL limité aux opérations nécessaires et TLS vers PostgreSQL.

Documentation OpenAPI : /docs. Vérification de disponibilité : /health.

## Tests

Depuis le répertoire backend (tests unitaires en mémoire) :

    python -m pytest -v

Le test réel de persistance SQL est activé uniquement avec `TEST_DATABASE_URL` pointant sur une base PostgreSQL jetable après application de la migration SA-17. Il crée puis supprime un compte de test et contrôle inscription, lecture depuis une nouvelle instance du dépôt, connexion et validation du JWT depuis la ligne SQL persistée.
