# SmartCampus AI : API du catalogue (SA-20)

API FastAPI de gestion du catalogue de formations, basée sur le modèle SA-12
(établissements, formations/parcours, critères d'admission).

- **Aucune base de données** : les données sont gardées en mémoire et disparaissent à l'arrêt du serveur.
  Les établissements IIT (id 1) et ISB (id 2) sont créés au démarrage.
- Architecture en couches : routes -> service -> repository.
- Écriture réservée au rôle `admin`. Authentification TEMPORAIRE par l'en-tête `X-Role`
  (`visiteur`, `candidat`, `admin`) : le JWT sera fourni par SA-28 (seule `get_current_role()` changera).

## Lancer (Windows, cmd, depuis le dossier backend)

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    pytest
    uvicorn app.main:app --reload

Documentation interactive : http://127.0.0.1:8000/docs

## Tester avec Swagger

Les routes d'écriture demandent le champ `x-role` = `admin`.

1. `POST /api/v1/formations` (x-role = admin, `etablissement_id` = 1) : 201, statut BROUILLON.
2. `GET /api/v1/formations` sans rôle : liste vide (seules les formations PUBLIE sont publiques).
3. `PATCH /api/v1/formations/1` avec `{"statut": "PUBLIE"}` (admin) : la formation devient visible.
4. `GET /api/v1/formations` sans rôle : la formation apparaît.
5. `POST /api/v1/formations/1/criteres` (admin) : ajoute un critère d'admission.
6. `DELETE /api/v1/formations/1` (admin) : ARCHIVE la formation (elle n'est pas effacée).
7. Erreurs attendues : 403 (pas admin), 404, 409 (code_parcours déjà utilisé), 422 (données invalides),
   toutes au format `{"error": {"code": "...", "message": "..."}}`.

## Modèle de données (SA-12)

**Etablissement** : id, code (unique), nom, ville, site_web, est_actif.

**FormationParcours** : id, etablissement_id, code_parcours (unique), type_parcours (LICENCE, PREPA,
INGENIERIE, etc., en majuscules), titre, duree_semestres (> 0), resume, objectifs_pedagogiques,
debouches (texte), modalite, langue_enseignement, tags_interets (liste), statut (BROUILLON | PUBLIE |
ARCHIVE, défaut BROUILLON), source_reference, source_url, derniere_synchro_at.

**CritereAdmission** : id, parcours_id, niveau_requis, filieres_acceptees (liste), score_ou_moyenne_min
(0 à 999.99), prerequis_matieres, modalites_admission, priorite (défaut 1).

La table `documents_catalogue_rag` (corpus RAG, pgvector) est hors périmètre de SA-20.

## Routes (/api/v1)

| Méthode | Route | Rôle |
|---|---|---|
| POST | /formations | admin |
| GET | /formations (filtres : etablissement, type_parcours, limit, offset ; statut = admin) | tous |
| GET | /formations/{id} | tous (PUBLIE) / admin (tous statuts) |
| PATCH | /formations/{id} | admin |
| DELETE | /formations/{id} (archive) | admin |
| GET / POST | /formations/{id}/criteres | tous / admin |
| GET / PATCH / DELETE | /criteres/{id} | tous / admin / admin |
| GET | /etablissements | tous |

Règles : visibilité publique = formations PUBLIE d'un établissement actif ; code_parcours unique ;
l'établissement doit exister et être actif ; DELETE archive au lieu d'effacer.

## Brancher une vraie base plus tard

Toute la gestion du stockage est dans `app/repositories/formation_repository.py`
(classe `InMemoryCatalogueRepository`). Une autre classe avec les mêmes méthodes pourra la remplacer
dans `app/api/dependencies.py` sans modifier les routes ni le service.

## Points à valider (non tranchés)

- Liste complète des valeurs de `type_parcours` (notamment ISB) : pas de liste fermée pour l'instant.
- Aucune table de tarifs dans SA-12 alors que SA-19 parle de tarifs officiels.
- Nom officiel de l'ISB, ville et sites web (données de départ provisoires).
- Partage des GET des critères avec SA-21 (consultation des conditions d'admission).
