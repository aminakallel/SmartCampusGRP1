# SA-29 — Rattachement conversation visiteur → compte

## État du travail

Décision de compatibilité retenue pour les prototypes : `session_id` UUID v4, `conversation_id`, `created_at` et `expires_at` SA-25 sont canoniques; la mémoire SA-26 reçoit exactement ces valeurs; SA-29 prend l’identifiant de compte depuis une dépendance Bearer vérifiant un JWT SA-28 valide, jamais depuis le corps fourni par le client. Le compte est persistant dans PostgreSQL; la session et la mémoire restent locales au processus.

## Scénario couvert

1. Un visiteur possède une session UUID v4, une conversation et des messages anonymes.
2. Après inscription ou connexion, l’authentification fournit l’identifiant UUID du compte au service SA-29.
3. Le service vérifie que la session et la mémoire ont les mêmes `session_id`, `conversation_id`, `created_at` et `expires_at`, puis les rattache au compte avec un même `attached_at`.
4. Répéter le rattachement vers le même compte est idempotent ; un autre compte ne peut pas reprendre la session.
5. Une session expirée ou inconnue ne peut pas être rattachée.

Les tests utilisent des UUID et des messages fictifs. Le parcours d’intégration remplace uniquement la dépendance SA-28 par un compte de test; aucun jeton fictif n’est accepté comme authentification réelle.

## Contrats à valider avant l’API réelle

- Persistance SQL (SA-17 / intégration Yasmine) : remplacer le dépôt utilisateur et les stores locaux par la transaction SQL commune et confirmer le schéma de déploiement.
- Yasmine : persister ensemble `session_visiteur.utilisateur_id`, `rattachee_le`, `conversation_id` et la propriété de la mémoire, dans une transaction SQL.
- L’API provisoire est `POST /api/v1/chat/rattacher`, avec `X-Session-ID` et Bearer. Elle retourne 404 pour une session/mémoire absente ou expirée, 409 pour une incohérence/conflit, et marque un nouvel attachement comme idempotent.

Le schéma SA-26 utilise maintenant `session_id` UUID v4, `conversation_id`, `messages` (`role`, `content`, `timestamp`, `metadata`), `temporary_info`, `created_at`, `expires_at`, `account_id` et `attached_at`. La mémoire conserve au plus les 20 derniers messages, mais n’a plus de TTL glissant indépendant. Une session SA-25 crée la mémoire; la supprimer supprime aussi cette mémoire. Les messages au-delà de la limite de 20 restent supprimés selon la règle SA-26.

## Revue de conformité et compatibilité

| Règle ou relation | Résultat | Portée vérifiée / limite |
|---|---|---|
| SA-25 : session visiteur et identité | Conforme dans le stockage simulé | UUID v4 et `conversation_id` proviennent de la session; les métadonnées de compte/rattachement y sont enregistrées. |
| SA-26 : identité, conversation, dates partagées | Conforme dans le stockage simulé | La mémoire est initialisée lors de la création SA-25; UUID v4, `conversation_id`, dates de création et d’expiration sont identiques. Les routes SA-26 refusent les identifiants non UUID ou les mémoires absentes/expirées. |
| SA-13 : compte `utilisateur.id` de type UUID | Conforme au type déclaré | Le compte n’est restreint à aucune version d’UUID, car le modèle SA-13 spécifie UUID sans contrainte de version. Le service exige que l’appelant lui fournisse un objet UUID. |
| SA-13 : lien session visiteur → utilisateur et date | Conforme en mémoire | Les champs `account_id` et `attached_at` reflètent `utilisateur_id` et `rattachee_le`; aucune FK SQL n’est exécutée. |
| Conservation du contexte et de l’ordre des messages | Conforme en mémoire | Le parcours appelle le vrai endpoint SA-29 et vérifie que les objets SA-26 restent inchangés et attachés au même compte. |
| Session absente/expirée | Conforme dans le service simulé | Refus avec erreur métier et suppression du contexte expiré; SA-25 purge également les sessions expirées à la lecture. |
| Rattachement répété au même compte | Conforme dans le stockage simulé | Idempotent : même conversation, historique et date initiale de rattachement. |
| Rattachement concurrent / idempotence | Conforme dans les dépôts simulés | Les tests couvrent les retries, le conflit d’un autre compte et le rollback en cas d’échec mémoire. La transaction SQL multi-processus reste à faire. |
| Authentification SA-28 | JWT actif dans le prototype | Inscription et connexion émettent un Bearer signé HS256; `/auth/me` et SA-29 vérifient signature, expiration, émetteur, utilisateur actif et rôle. Les sessions fournies sont rattachées après inscription ou connexion. Le dépôt utilisateur reste en mémoire. |
| Persistance du compte SA-28 | Conforme à la migration SA-17 | Le dépôt authentification lit et écrit `public.utilisateur`; le test d'intégration vérifie la relecture avec une nouvelle instance et la connexion par JWT après persistance SQL. |
| Persistance de la session et de la mémoire SA-25/26/29 | Non implémentée | Ces stores restent en mémoire; les liens et messages ne survivent pas à un redémarrage. La transaction commune et les FK de rattachement doivent encore être intégrées. |

### Contrôles exécutés

- Cas nominaux visiteur → compte, conservation des messages et de l’identifiant conversation.
- Compatibilité avec création/suppression SA-25, écriture/lecture SA-26, et l’endpoint SA-29 protégé par la frontière Bearer.
- Idempotence, session inconnue/expirée, conflit de propriétaire et deux demandes concurrentes.
- Type UUID du compte sans restriction de version, UUID v4 obligatoire pour la session, dates timezone-aware, cohérence `account_id`/`attached_at`, conversation non vide et unicité de la session dans le dépôt simulé.
- Suite backend complète après harmonisation des contrats : 58 tests, dont l'intégration PostgreSQL SA-28 (SA-25, SA-26, SA-28 et SA-29).

Le scénario combiné utilise les routes SA-25, SA-26, SA-28 et SA-29; SA-28 est validée avec PostgreSQL temporaire, et les stores SA-25/26/29 demeurent simulés. La limite SA-26 de 20 messages signifie que SA-29 rattache exactement la mémoire encore conservée, pas les messages déjà écartés par cette limite.

## Exécution des tests

Depuis `backend` :

    python -m pytest -q

Le test de production doit attendre la transaction SQL commune pour la session et la mémoire, ainsi que l'injection de `DATABASE_URL` et de `JWT_SECRET` dans le gestionnaire de secrets du déploiement.
