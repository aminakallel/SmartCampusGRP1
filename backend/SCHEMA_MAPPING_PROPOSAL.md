# Proposition de mapping des schémas — non validée

Cette proposition est une comparaison des documents fournis, pas une décision de l’équipe. Aucun modèle ORM, FK métier ou migration de tables ne doit être construit à partir de ce document avant validation des propriétaires concernés.

## Sources et attribution

| Document reçu | Contenu constaté | Attribution disponible |
|---|---|---|
| `Conception-des-tables-utilisateurs-et-profils.pdf` (7 pages) | SA-13 : comptes, profils, résultats, intérêts, sessions visiteurs et DDL de référence | Métadonnées auteur vides; périmètre Manar d’après la répartition fournie |
| `Acteurs-et-processus-métiers.pdf` (4 pages) | Visiteur/candidat/admin, conversation temporaire, profil, candidature, QCM et entretien | Pas d’auteur ni de tâche indiqués; correspond au périmètre métier indiqué pour Manar |
| `ArchitectureGlobale_SmartCompus-1.pdf` (7 pages) | Architecture SA-4, REST/SSE, agents, PostgreSQL/pgvector, règles d’orchestration | Métadonnées auteur vides; responsabilité architecture attribuée à Tasnime dans la répartition |
| `Concevoir_les_tables_du_catalogue_académique.pdf` (3 pages) | Établissements, parcours, critères, corpus RAG/pgvector | Métadonnées auteur vides; responsabilité catalogue attribuée à Tasnime dans la répartition |
| `Contrat_d_Interface_API_et_Règles_d_Accès-1.pdf` (9 pages) | SA-5 : méthodes, routes, rôles, validations, formats JSON, erreurs | Métadonnées : « Équipe SmartCampus AI »; la mission attribue l’API et les règles à Amina |
| `SA-14_Conception_Tables_Gestion.md` | Préinscriptions, compléments, QCM, rendez-vous; cinq tables et DDL de référence | Le document nomme Amina Kallel comme responsable SA-14 |

Aucun document de conception distinct de Roua sur le frontend ou la mémoire temporaire des conversations n’a été fourni. Les exigences d’interface disponibles viennent du document SA-5 et de l’architecture globale.

## Comparatif des tables et relations

### SA-13 — utilisateurs, profils et sessions (document attribué à Manar)

| Table | Colonnes et types documentés | Clés et relations | Notes / incompatibilités |
|---|---|---|---|
| `utilisateur` | `id UUID`; `nom VARCHAR(100)`; `prenom VARCHAR(100)`; `email VARCHAR(255)`; `mot_de_passe_hash VARCHAR(255)`; `role role_utilisateur`; `langue_preferee langue_echange`; `est_actif BOOLEAN`; `derniere_connexion TIMESTAMPTZ`; `cree_le TIMESTAMPTZ`; `modifie_le TIMESTAMPTZ` | PK `id`; index unique sur `lower(email)`; rôles `candidat/admin` | Le SA-14 d’origine nommait cette table `users`; la décision de coordination a confirmé `utilisateur` et le mapping SA-14 plus bas l’applique. L’API montre `usr_…` sans préciser si c’est une clé opaque ou l’UUID stocké. Les rôles `system_webhook/internal_agent` restent des identités de service hors de l’enum utilisateur. |
| `profil_candidat` | `id UUID`; `utilisateur_id UUID`; `telephone VARCHAR(20)`; `date_naissance DATE`; `ville VARCHAR(100)`; `gouvernorat VARCHAR(50)`; `pays VARCHAR(60)`; `adresse TEXT`; `niveau_etudes VARCHAR(100)`; `serie_bac VARCHAR(60)`; `etablissement_origine VARCHAR(150)`; `annee_obtention SMALLINT`; `moyenne_generale NUMERIC(4,2)`; `objectifs TEXT`; `etablissement_prefere etablissement_cible`; `mode_contact_prefere mode_contact`; `cree_le/modifie_le TIMESTAMPTZ` | PK `id`; FK unique `utilisateur_id → utilisateur.id`, `ON DELETE CASCADE`; relation utilisateur 1 à 0..1 profil | SA-5 demande `niveau_scolaire` énuméré, `specialite_origine`, `objectifs_professionnels` (10–500 caractères), et `interets` non vide. Il faut valider les alias/règles vers `niveau_etudes`, `serie_bac`, `objectifs`; `specialite_origine` n’existe pas sous ce nom dans SA-13. |
| `resultat_scolaire` | `id UUID`; `profil_id UUID`; `matiere VARCHAR(100)`; `periode VARCHAR(50)`; `note NUMERIC(4,2)`; `coefficient NUMERIC(4,2)` | PK `id`; FK `profil_id → profil_candidat.id`, cascade; unique `(profil_id, matiere, periode)` | Note entre 0 et 20; coefficient > 0, défaut 1. Le profil est complet avec au moins un résultat. |
| `interet` | `id UUID`; `libelle VARCHAR(100)`; `categorie VARCHAR(60)` | PK `id`; `libelle` unique | SA-5 décrit une liste de chaînes; il faut convenir si seules les références existantes sont acceptées ou si l’API peut créer un intérêt. |
| `profil_interet` | `profil_id UUID`; `interet_id UUID`; `ajoute_le TIMESTAMPTZ` | PK composée `(profil_id, interet_id)`; FK profil cascade; FK intérêt restrict; relation N–N | L’intérêt est une entité de référence et non une colonne libre du profil. |
| `session_visiteur` | `session_id UUID`; `utilisateur_id UUID NULL`; `cree_le TIMESTAMPTZ`; `expire_le TIMESTAMPTZ`; `rattachee_le TIMESTAMPTZ NULL` | PK `session_id`; FK nullable vers `utilisateur.id`, `ON DELETE SET NULL`; utilisateur 1 à N sessions | La session est un UUID v4. `X-Session-Id` et `X-Session-ID` sont équivalents (les noms d’en-tête HTTP sont insensibles à la casse). La table ne contient pas les messages/conversations. |

Types/enums mentionnés par SA-13 : `role_utilisateur` (`candidat`, `admin`), `langue_echange` (`fr`, `tunisien`, `arabizi`), `etablissement_cible` (`IIT`, `ISB`, `indifferent`), `mode_contact` (`email`, `telephone`). Le DDL PDF utilise des apostrophes typographiques dans plusieurs littéraux; il doit être normalisé en SQL ASCII avant exécution et relu par Manar.

### Catalogue académique — document attribué à Tasnime

| Table | Colonnes et types documentés | Clés et relations | Notes / incompatibilités |
|---|---|---|---|
| `etablissements` | `id SERIAL`; `code VARCHAR(20)`; `nom VARCHAR(150)`; `ville VARCHAR(100)`; `site_web VARCHAR(255) NULL`; `est_actif BOOLEAN` | PK `id`; `code` unique; 1 établissement à N parcours | Le code IIT/ISB est un code métier distinct de l’ID SERIAL. |
| `formations_parcours` | `id SERIAL`; `etablissement_id INTEGER`; `code_parcours VARCHAR(40)`; `type_parcours VARCHAR(30)`; `titre VARCHAR(200)`; `duree_semestres SMALLINT`; `resume TEXT`; `objectifs_pedagogiques TEXT`; `debouches TEXT`; `modalite VARCHAR(50)`; `langue_enseignement VARCHAR(50)`; `tags_interets JSONB`; `statut VARCHAR(20)`; `source_reference VARCHAR(255)`; `source_url VARCHAR(255)`; `derniere_synchro_at TIMESTAMPTZ` | PK `id`; FK `etablissement_id → etablissements.id`; `code_parcours` unique | Le SA-14 d’origine référençait `formations(id UUID)`; la coordination confirme désormais `formations_parcours(id SERIAL/INTEGER)`, appliqué aux FK proposées plus bas. L’API montre `form_…` sans préciser son type public. |
| `criteres_admission` | `id SERIAL`; `parcours_id INTEGER`; `niveau_requis VARCHAR(100)`; `filieres_acceptees JSONB`; `score_ou_moyenne_min NUMERIC(5,2) NULL`; `prerequis_matieres TEXT`; `modalites_admission TEXT`; `priorite SMALLINT` | PK `id`; FK `parcours_id → formations_parcours.id`, cascade; parcours 1 à N critères | Les détails JSON et validations API restent à convenir. |
| `documents_catalogue_rag` | `id SERIAL`; `parcours_id INTEGER`; `type_source VARCHAR(40)`; `titre_source VARCHAR(200)`; `extrait_url_ou_ref VARCHAR(255)`; `contenu_chunk TEXT`; `embedding vector(1536) NULL` | PK `id`; FK `parcours_id → formations_parcours.id`, cascade; parcours 1 à N extraits | Nécessite pgvector et une dimension 1536 cohérente avec le service RAG. L’image actuelle `postgres:16-alpine` ne fournit pas pgvector. |

Règle catalogue : seuls les parcours `PUBLIE` liés à un établissement actif sont publics; CRUD, critères et corpus RAG sont administrateur seulement; les réponses RAG citent une source officielle.

### SA-14 — préinscriptions, QCM et rendez-vous (Amina Kallel)

| Table | Colonnes et types documentés | Clés et relations | Notes / incompatibilités |
|---|---|---|---|
| `dossier_candidature` | `id UUID`; `utilisateur_id UUID`; `parcours_id INTEGER`; `source_webhook_id VARCHAR(100) NULL`; `donnees_admin_json JSONB`; `resume_ia JSONB NULL`; `statut statut_dossier`; `decision_par_admin_id UUID NULL`; `commentaire_admin TEXT NULL`; `soumis_le/modifie_le TIMESTAMPTZ` | PK `id`; FK unique `utilisateur_id → utilisateur.id UUID`, cascade; FK `parcours_id → formations_parcours.id INTEGER`, restrict; FK décisionnaire nullable → `utilisateur.id UUID`, set null; `source_webhook_id` unique nullable | Nouveau SA-14 reçu le 22 novembre; un seul dossier par utilisateur est imposé. |
| `dossier_complement` | `id UUID`; `dossier_id UUID`; `demande_admin TEXT`; `reponse_candidat TEXT NULL`; `piece_jointe_url VARCHAR(500) NULL`; `est_resolu BOOLEAN`; `cree_le/repondu_le TIMESTAMPTZ` | PK `id`; FK `dossier_id → dossier_candidature.id`, cascade; dossier 1 à N compléments | Nom de table singulier dans la nouvelle version. |
| `qcm_tentative` | `id UUID`; `dossier_id UUID`; `parcours_cible_id INTEGER`; `statut statut_qcm`; `derniere_question_idx INTEGER`; `nb_total_questions INTEGER`; `score_pourcentage NUMERIC(5,2) NULL`; `synthese_acquis_ia TEXT NULL`; `cree_le/modifie_le/termine_le TIMESTAMPTZ` | PK `id`; FK dossier cascade; FK `parcours_cible_id → formations_parcours.id INTEGER`, restrict; dossier 1 à N tentatives | Nouvelle version SA-14 alignée sur la PK INTEGER du catalogue. |
| `qcm_question` | `id UUID`; `tentative_id UUID`; `ordre INTEGER`; `enonce TEXT`; `options_json JSONB`; `bonne_option_id VARCHAR(10)`; `reponse_candidat_id VARCHAR(10) NULL`; `est_correcte BOOLEAN NULL` | PK `id`; FK `tentative_id → qcm_tentative.id`, cascade; unique `(tentative_id, ordre)`; tentative 1 à N questions | La relation 1..N indiquée dans le diagramme n’est pas garantie pour au moins une question par le DDL. |
| `rendez_vous` | `id UUID`; `dossier_id UUID`; `admin_id UUID NULL`; `date_heure_debut/fin TIMESTAMPTZ`; `modalite modalite_rdv`; `lien_ou_salle VARCHAR(255) NULL`; `valide_par_admin BOOLEAN`; `statut statut_rdv`; `motif_indisponibilite TEXT NULL`; `cree_le/modifie_le TIMESTAMPTZ` | PK `id`; FK dossier cascade; FK admin → `utilisateur.id UUID`, set null; dossier 1 à N rendez-vous | La validation de rôle admin ne garantit pas que l’admin référence l’état du rendez-vous ni que chaque rendez-vous confirmé possède un admin. |

États SA-14 : dossier `soumis`, `complement_demande`, `accepte`, `refuse`; rendez-vous `propose`, `confirme`, `indisponible`; QCM `en_cours`, `termine`. La décision d’admission reste humaine. Le nouveau Markdown contient le SQL de migration en section 4, mais le fichier `.sql` autonome annoncé n’est pas présent dans le checkout.

## Contrat d’interface (SA-5) et écarts avec le backend livré

- Routes métier préfixées `/api/v1`; échanges JSON et streaming conversationnel SSE.
- Authentification utilisateur : `Authorization: Bearer`; visiteur : UUID v4 dans `X-Session-ID`; webhook : `X-Webhook-Secret`; outils agents : `X-Internal-API-Key`.
- Rôles : `visiteur`, `candidat`, `admin`, plus `system_webhook` et `internal_agent` pour des accès de service. Un candidat n’accède qu’à ses propres ressources; résumé IA et historique complet sont réservés à l’admin.
- Ressources contractuelles : `/auth/register|login|me`, `/chat`, `/chat/historique`, `/chat/rattacher`, `/formations`, `/candidats/{id}/profil|recommandations|conversations|dossier|qcm`, `/preinscriptions/lien|webhook`, `/dossiers`, `/qcm`, `/rendez-vous`, `/internal/tools/*`.
- Les réponses d’erreur SA-5 demandent `{ "error": { "code": ..., "message": ..., "details": {} } }`. Le backend livré n’avait que les routes de santé; ses erreurs utilisaient `detail`. Une enveloppe SA-5 vient d’être ajoutée pour les erreurs FastAPI et les validations 422; les endpoints métier restent absents.
- Les exemples API utilisent `usr_…`, `form_…`, `dos_…`, `qcm_…` alors que les schémas détaillés stockent UUID et SERIAL. Il faut déterminer si ces chaînes sont des identifiants publics opaques ou de simples placeholders, sans les prendre pour des types SQL validés.

### Routes, paramètres, réponses et autorisations extraits de SA-5

Toutes les routes listées ci-dessous sont sous `/api/v1`. L’extraction ci-dessous reprend le contrat fourni; elle ne prétend pas que ces routes existent dans l’implémentation actuelle.

| Méthode / route | Accès et paramètres/validation | Réponse ou règle relevée |
|---|---|---|
| `POST /auth/register` | `visiteur`; `email` valide/unique, `password` >= 8 caractères avec majuscule et chiffre, `nom`/`prenom` 2–50 caractères, `session_id` optionnel UUID v4 | Exemple 201: `access_token`, `token_type`, `user`, `conversation_rattachee` |
| `POST /auth/login` | `visiteur`; détail des champs non spécifié dans le document | Réponse de jeton mentionnée, schéma complet non donné |
| `GET /auth/me` | `candidat`, `admin`; Bearer JWT | Compte authentifié et rôle |
| `POST /chat` | `visiteur`, `candidat`; message 1–2000 caractères; session UUID requise au visiteur dans corps ou `X-Session-ID`; `stream` bool défaut `true` | JSON ou SSE; exemple JSON contient `conversation_id`, `reponse`, langue, sources RAG, complétude et champs manquants |
| `GET /chat/historique` | `visiteur`, `candidat`; session courante via header ou compte JWT | Messages de la session courante; corps précis non spécifié |
| `POST /chat/rattacher` | `candidat`; rattache `session_id` anonyme au compte connecté | Schéma détaillé non spécifié |
| `GET /formations` | Public : visiteur/candidat/admin; filtres query d’établissement IIT/ISB et cycle | Liste; seules formations `PUBLIE` d’un établissement actif |
| `GET /formations/{id}` | Public : visiteur/candidat/admin | Détails conditions d’accès, durée, programme, débouchés |
| `POST /formations` | Admin |  Création puis indexation RAG; payload/réponse détaillés non spécifiés |
| `PATCH /formations/{id}` | Admin | Mise à jour partielle selon la décision de coordination; payload/réponse détaillés non spécifiés |
| `DELETE /formations/{id}` | Admin | Suppression du catalogue et de l’index RAG |
| `GET /candidats/{id}/profil` | Candidat propriétaire ou admin | Profil scolaire, intérêts et objectifs |
| `PUT /candidats/{id}/profil` | Candidat propriétaire; `niveau_scolaire` enum (`bac`, `licence_1`, `licence_2`, `licence_3`, `prepa`, `autre`), `specialite_origine` requis, `moyenne_generale` 0–20 optionnelle, `interets` non vide, `objectifs_professionnels` 10–500 caractères | Mise à jour et vérification de complétude; réponse exacte non fournie |
| `GET /candidats/{id}/recommandations` | Candidat propriétaire ou admin | Shortlist avec justification et score de compatibilité |
| `GET /candidats/{id}/conversations` | Admin | Historique brut complet |
| `GET /preinscriptions/lien` | Candidat | URL du formulaire externe préremplie avec identifiant candidat |
| `POST /preinscriptions/webhook` | `system_webhook`; header `X-Webhook-Secret` | Exemple 201; payload candidat, formation choisie, données administratives, timestamp; assemble le dossier et initialise le résumé/entretien |
| `GET /candidats/{id}/dossier` | Candidat propriétaire ou admin | État du dossier; `resume_ia` masqué au candidat |
| `GET /dossiers` | Admin; filtre statut | Liste dossiers |
| `GET /dossiers/{id}` | Admin | Dossier complet, données administratives et résumé IA |
| `PATCH /dossiers/{id}/statut` | Admin; `accepte`, `refuse` ou `complement_demande` avec commentaire éventuel | Changement d’état; décision exclusivement humaine |
| `POST /dossiers/{id}/complements` | Candidat propriétaire | Réponse aux compléments demandés; schéma précis non fourni |
| `GET /candidats/{id}/qcm` | Candidat propriétaire | QCM et dernière progression |
| `POST /qcm/{id}/progression` | Candidat propriétaire; `question_index >= 0`; QCM doit être `en_cours` | Sauvegarde; modification d’un QCM terminé = 400; exemple retourne statut/progression/date |
| `POST /qcm/{id}/soumettre` | Candidat propriétaire | Valide, calcule score et synthèse; détails JSON non fournis |
| `GET /dossiers/{id}/qcm-resultats` | Admin | Questions/réponses et analyse des acquis |
| `GET /rendez-vous` | Candidat (ses rendez-vous) ou admin (globaux/filtres) | Liste |
| `POST /rendez-vous/{id}/confirmer` | Admin | Confirme le créneau avant notification au candidat |
| `POST /rendez-vous/{id}/reponse-candidat` | Candidat propriétaire; décision `confirme` ou `indisponible`; motif/disponibilités >= 5 caractères si indisponible | Exemple indique statut et notification admin |
| `POST /internal/tools/save-message` | Service interne avec `X-Internal-API-Key` | Enregistre un tour associé à session ou candidat |
| `GET /internal/tools/get-profile/{id}` | Service interne | Lit les données académiques/completude du candidat |
| `POST /internal/tools/save-recommendations` | Service interne | Persiste shortlist et justifications RAG |
| `POST /internal/tools/save-dossier-summary` | Service interne | Persiste résumé structuré |
| `POST /internal/tools/propose-slots` | Service interne | Produit des créneaux proposés pour validation admin |
| `POST /internal/tools/send-email` | Service interne | Envoie notifications; aucun email réel pendant les tests |

Les erreurs SA-5 (400, 401, 403, 404, 422, 500) utilisent `{ "error": { "code": "...", "message": "...", "details": {} } }`. L’architecture SA-4 montre un exemple abrégé sans `details`; le document contractuel SA-5 fournit le schéma détaillé à retenir.

## Mapping de coordination (choix confirmés; autres décisions en attente)

Décisions de coordination rapportées le 22 novembre 2026 : Manar confirme `utilisateur`; Tasnime confirme `SERIAL` (SQL `INTEGER`) pour l’ID Formation et `PATCH`; Amina s’aligne. Ces trois points sont appliqués dans cette proposition. Les documents source SA-14 et SA-5 ne sont pas réécrits ici; ils conservent leurs anciennes mentions `PUT`, `users` et UUID Formation et doivent être actualisés par leurs propriétaires pour éviter une divergence documentaire.

1. Nom canonique compte : `utilisateur`; PK UUID.
2. Nom canonique catalogue : `formations_parcours`; PK SERIAL / INTEGER.
3. Appliquer à SA-14 les FK candidat/admin UUID vers `utilisateur.id` et les FK Formation INTEGER vers `formations_parcours.id`.
4. Route de mise à jour Formation : `PATCH /api/v1/formations/{id}`.
5. Après confirmation des décisions restantes ci-dessous, écrire migrations de tables, modèles ORM et seed relationnel dans l’ordre des FK. Ne pas créer de tables parallèles `users` ou `formations`.

## Validations requises

| Décision | Validation demandée |
|---|---|
| Nom canonique utilisateur `utilisateur` et PK UUID | **Confirmé** — Manar; Amina alignée |
| Nom canonique Formation `formations_parcours`, PK SERIAL/INTEGER | **Confirmé** — Tasnime; Amina alignée |
| Route de mise à jour Formation `PATCH` | **Confirmé** — Tasnime; Amina alignée; document SA-5 source à actualiser |
| Types d’IDs exposés par les exemples JSON et la conversion API/DB | Amina + responsables des schémas concernés |
| Reporter dans les documents SA-14/SA-5 les références `utilisateur`, FK Formation INTEGER et `PATCH` | Amina + Tasnime |
| Mapping `niveau_scolaire`, `specialite_origine`, `objectifs_professionnels`, intérêts vers SA-13 | Manar + Amina |
| Un dossier maximum par utilisateur (`UNIQUE(utilisateur_id)`) ou plusieurs | Amina + Manar |
| Extension pgvector, version d’image Postgres et dimension réelle des embeddings (1536) | Tasnime + propriétaire du service RAG |
| Format de stockage temporaire des messages et rattachement visiteur→compte | Roua + Manar + Backend |

## Périmètre d’implémentation déjà autonome

- Le backend livré sur `yasmin` contient uniquement `/health` et `/health/db`, configuration, SQLAlchemy et seed de staging.
- L’enveloppe d’erreur SA-5 et les tests de non-divulgation/validation sont traités séparément des schémas métier.
- Une migration technique d’extensions (`pgcrypto`, `vector`) peut être préparée, mais ne doit pas être exécutée contre la base locale sans vérifier que le serveur cible fournit pgvector. Elle ne crée pas de table métier.
- Le seed de staging n’est pas un seed métier; aucune exécution réelle n’est autorisée avant le mapping validé.

## Inventaire du code Tasnime dans les sources disponibles

La recherche a été faite dans le checkout `yasmin`, les fichiers suivis par Git, la branche locale `origin/tasnime` disponible et les fichiers trouvés dans le dossier de projet. Les sept fichiers annoncés ne sont pas présents dans ces sources :

| Fichier annoncé | Présence vérifiée |
|---|---|
| `schemas/formation.py` | Absent |
| `api/v1/formations.py` | Absent |
| `core/security.py` | Absent |
| `services/formation_service.py` | Absent |
| `repositories/formation_repository.py` | Absent |
| `core/errors.py` | Absent |
| `api/responses.py` | Absent |

La branche `origin/tasnime` disponible localement ne contient que `README.md`. Les pièces jointes disponibles contiennent la conception catalogue et l’architecture, mais aucun code Python Tasnime ni son dernier tableau séparé. Les responsabilités de ces fichiers sont donc décrites par la mission de Yasmin; leur implémentation, signatures, validations, règles anti-doublon et comportements runtime ne peuvent pas être présentés comme audités.

Le backend Yasmin réellement présent expose seulement `/health` et `/health/db`; il fournit déjà `Base`, `engine`, `SessionLocal` et la dépendance de session `get_db()` dans `app/db/database.py`. Il n’existe pas encore de routeur métier Formation, modèle ORM Formation, repository Python en dictionnaire, service métier ou contrôle Admin dans ce checkout. En conséquence, aucun fichier de Tasnime n’a été remplacé ou modifié.

## Adaptation PostgreSQL proposée pour le repository Formation

Cette séquence est préparatoire et n’implique pas que le schéma soit accepté :

1. Garder le routeur Tasnime comme propriétaire des routes; le monter sous `/api/v1` une fois son vrai code disponible. Les écritures restent Admin uniquement. La décision de coordination retient `PATCH` pour la mise à jour; le PDF SA-5 source qui documente `PUT` doit être actualisé par Amina.
2. Remplacer la dépendance à un dictionnaire global par un repository recevant la `Session` SQLAlchemy issue de `Depends(get_db)`. Garder la même interface de service/route et les mêmes DTO publics si possible; ne pas faire de SQL ou de `commit()` dans le routeur.
3. Après approbation du schéma, introduire le modèle SQLAlchemy correspondant à `formations_parcours` et ses liens vers `etablissements`, puis des méthodes repository explicites (`list`, `get`, `create`, `update`, `delete`). Le modèle et le repository devront partager la même session request-scoped; commit/rollback doit être transactionnel et fermer la session via `get_db()`.
4. Remplacer la détection de doublon en mémoire par une contrainte unique PostgreSQL sur la clé métier approuvée, avec conversion d’IntegrityError en erreur métier commune. Le document catalogue cite `code_parcours` unique; vérifier si l’unicité est globale ou composée avec établissement/type avant de poser la contrainte.
5. Ne jamais exposer implicitement un entier `SERIAL` sous forme `form_…`. La décision sur le type des IDs de route/JSON reste à faire confirmer par Amina; si des IDs opaques sont exigés, définir une colonne ou table de correspondance explicite plutôt qu’un encodage tacite.
6. Garder la vérification Admin dans une dépendance d’autorisation réutilisable; les opérations d’écriture doivent retourner 401 si non authentifié et 403 si authentifié sans rôle Admin. Le nom et la source réelle du rôle doivent s’aligner sur Manar/Amina avant d’écrire la dépendance.

Le format SA-5 `{ "error": { "code": ..., "message": ..., "details": ... } }` est déjà appliqué au socle FastAPI. Le module `core/errors.py` Tasnime n’étant pas disponible, on ne peut pas comparer son format réel. Il faudra soit faire appeler le handler commun du backend par ses routes, soit adapter son module vers la même fabrique; éviter deux enveloppes différentes.

## Mapping technique résultant des décisions (aucune migration autorisée/exécutée)

- Noms canoniques retenus : `utilisateur`, `profil_candidat`, `resultat_scolaire`, `interet`, `profil_interet`, `session_visiteur`; `etablissements`, `formations_parcours`, `criteres_admission`, `documents_catalogue_rag`; et les cinq tables SA-14.
- Types retenus : UUID pour PK utilisateur/gestion, SERIAL/INTEGER pour PK catalogue. Les FK SA-14 sont `utilisateur_id UUID → utilisateur.id UUID`, `parcours_id INTEGER → formations_parcours.id INTEGER`, `qcm_tentative.parcours_cible_id INTEGER → formations_parcours.id INTEGER`, `admin_id UUID → utilisateur.id UUID`.
- Les documents SA-14 et SA-5 fournis restent des sources historiques et n’ont pas été édités; leurs références `users`, Formation UUID et `PUT` sont incompatibles avec la coordination confirmée et doivent être mises à jour par leurs responsables.
- Garder les exemples `usr_…`/`form_…` au niveau API comme non spécifiés tant qu’Amina n’a pas confirmé leur sémantique; ne pas les utiliser directement comme valeurs de FK PostgreSQL.
- Le verbe Formation retenu est `PATCH`; aligner le préfixe `/api/v1`, l’enveloppe d’erreur et les réponses Swagger dans les fichiers API quand ils seront disponibles.

Les trois décisions de coordination ci-dessus sont confirmées; les autres éléments métier du mapping (notamment IDs publics JSON, unicité des dossiers et détail des champs profil) restent à valider. Ce document ne crée ni migration ni modification de données.

## Références historiques à mettre à jour dans les sources

Les choix métier sont résolus par la coordination, mais les pièces jointes originales restent inchangées et contiennent encore ces anciennes mentions. Elles ne sont pas des références à réintroduire dans le code :

| Source originale | Référence encore présente | État après décision |
|---|---|---|
| `SA-14_Conception_Tables_Gestion.md` (version précédente) | Noms de tables et colonnes d’une version antérieure | Supplantée par le nouveau SA-14 joint : `utilisateur_id`, `parcours_id`, `parcours_cible_id`, avec types UUID/INTEGER alignés. Ne pas mélanger les versions. |
| `Contrat_d_Interface_API_et_Règles_d_Accès-1.pdf` (SA-5) | `PUT /api/v1/formations/{id}` | Le contrat commun retient `PATCH /api/v1/formations/{id}`; Amina doit reporter la décision dans le document source/contrat versionné. |
| Checkout `yasmin` | Aucune occurrence de `users(id)`, FK Formation UUID ou route Formation `PUT` dans le code actuel; ces choix métier ne sont pas encore implémentés. | Aucun changement applicatif demandé dans cette mise à jour; aucune migration métier créée. |
