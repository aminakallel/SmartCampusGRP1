# Backend SA-25 — Sessions visiteur

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

Le service crée un identifiant de conversation opaque, mais ne stocke aucun message. La convention provisoire est documentée ci-dessus.

## Lancement local

Depuis le répertoire backend :

    python -m pip install -r requirements.txt
    uvicorn app.main:app --reload

Documentation OpenAPI : /docs. Vérification de disponibilité : /health.

## Tests

Depuis le répertoire backend :

    python -m pytest -v
