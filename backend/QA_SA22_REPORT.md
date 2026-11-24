# Rapport QA — SA-22 (QA des API)

Date de validation : 24 novembre 2026
Branche : `yasmin`
Verdict : **DONE pour le lot d'API actuellement livré, conformément à la QA progressive; les scénarios des API non encore livrées restent préparés pour les prochains incréments.**

## Exigences et périmètre vérifiable

La répartition Sprint 1 (fiche SA-22, page 4) demande de vérifier le fonctionnement et la sécurité des API : codes HTTP, validation, erreurs, droits d'accès, données retournées et cas limites; produire une collection de tests (Postman/pytest), un rapport d'anomalies et des preuves de correction. Elle demande de préparer les scénarios avant disponibilité des endpoints puis de les exécuter au fur et à mesure. Elle identifie des dépendances envers les API catalogue/auth (Tasnime), sessions/comptes (Manar) et règles d'accès/endpoints métier (Amina). Aucun critère Jira plus détaillé distinct n'a été trouvé.

L'inventaire de `app/main.py` confirme uniquement quatre routes API applicatives :

| Route | Comportement implémenté | Couverture/résultat |
|---|---|---|
| `GET /health` | Disponibilité du backend | HTTP 200 testé |
| `GET /health/db` | `SELECT 1`; indisponibilité convertie en 503 | 200 et 503 testés avec connexion simulée; pas une preuve de connexion PostgreSQL réelle |
| `GET /api/v1/catalogue/programmes` | Liste, filtres établissement/niveau, recherche `q` | HTTP 200, résultats vides, validation 422, limites de recherche, réponse publique testés |
| `GET /api/v1/catalogue/programmes/{slug}` | Détail d'un élément public | HTTP 200 et 404 (slug inexistant, brouillon/archivé/inactif) testés |

`/docs` et `/openapi.json` sont disponibles et testés, mais ce ne sont pas des API métier. Aucun endpoint d'authentification, d'inscription, de gestion des formations, de dossiers, de QCM, de rendez-vous, de chat, de recommandations ou d'outils internes n'est enregistré dans l'application locale. Aucun faux endpoint n'a été créé.

## Scénarios catalogue SA-22

`tests/test_sa22_catalogue_contract.py` définit CAT-01 à CAT-18, soit **22 cas pytest** après paramétrage. Les cas utilisent un dépôt mock isolé et des fichiers JSON temporaires.

| Scénarios | Vérifications | Résultat |
|---|---|---|
| CAT-01 à CAT-02 | Filtres sans résultat; niveau inconnu | PASS |
| CAT-03 (2 cas), CAT-04 (2 cas) | Longueurs normalisées de `q`: 1/101 rejetées, 2/100 acceptées | PASS; les refus sont HTTP 422 avec enveloppe commune |
| CAT-05 (2 cas) | Recherche dans description et mots-clés | PASS |
| CAT-06 à CAT-08 | Catalogue vide, schéma public, égalité complète liste/détail | PASS |
| CAT-09 à CAT-11 | Archives, brouillons et établissement inactif masqués | PASS dans le mock |
| CAT-12 à CAT-13 | Filtre établissement invalide; lecture publique sans authentification | PASS |
| CAT-14 | Erreur du repository convertie en 500 assaini | PASS |
| CAT-15 à CAT-17 | `q` absent; vide/blanc rejeté; espaces autour d'un terme retirés | PASS |
| CAT-18 | Slug inexistant retourne 404 et l'enveloppe commune | PASS |

CAT-09 vérifie le comportement de visibilité défini par la conception SA-12; ce test du mock ne vaut pas confirmation officielle de l'implémentation SA-21 par Roua.

## Exécutions réelles

Exécution dans le venv WSL du projet : Ubuntu 24.04, Python 3.12.3, FastAPI 0.115.12, HTTPX 0.28.1, pytest 8.3.5, Starlette 0.46.2.

| Commande | Résultat |
|---|---|
| `python -m pip check` | `No broken requirements found` |
| `python -m pytest -v tests/test_sa22_catalogue_contract.py` | **22 passed, 0 failed, 0 skipped, 1 warning** |
| `python -m pytest -v tests/test_health.py` | **16 passed, 0 failed, 0 skipped, 1 warning** |
| `python -m pytest -v` après intégration catalogue | **102 passed, 0 failed, 0 skipped, 1 warning** |

L'avertissement restant provient de Starlette : l'alias `anyio.abc.BlockingPortal` est déprécié en faveur de `anyio.from_thread.BlockingPortal`; il n'a fait échouer aucun test. Les assertions HTTP 422 de `q` ont été exécutées dans CAT-03, CAT-16 et CAT-17 et réussissent. Aucun cas des commandes ci-dessus n'a été ignoré ou bloqué.

Les tests ne se connectent pas à PostgreSQL : DB health et erreurs sont simulées; la suite complète ne lance aucune migration et n'insère aucune donnée. Les résultats antérieurs de 32/93 tests et de 21/98 tests sont des baselines précédentes, remplacées par les résultats ci-dessus pour le code de cette vérification.

## Anomalies et preuves de correction

- La revue QA avait identifié une lacune de couverture : le cas d'un slug inexistant n'était pas testé explicitement. CAT-18 a été ajouté pour vérifier HTTP 404 et l'enveloppe `NOT_FOUND`; le test passe dans les 22 cas catalogue et la suite complète de 99 tests.
- Aucun défaut de production n'a été reproduit dans les routes actuellement disponibles pendant cette vérification; aucune correction d'API n'a donc été nécessaire.
- Le plan de tests présentait certains scénarios catalogue déjà exécutés comme encore prêts/en attente. `CONTRACT_TEST_PLAN.md` a été ajusté pour distinguer la couverture réelle des scénarios différés.
- La relance de clôture du 24 novembre 2026 après intégration catalogue confirme `pip check` propre et **102 passed, 0 failed, 0 skipped**. La seule observation restante est l'avertissement de dépréciation Starlette/AnyIO décrit ci-dessus.

## Codes HTTP et erreurs

- **200** : santé et routes GET catalogue; contenu public et cohérence liste/détail vérifiés.
- **400, 401, 403, 503** : enveloppe testée via des routes temporaires dédiées au test du handler; cela vérifie l'infrastructure commune, pas une authentification ou une permission métier réelle. Le 400 CORS est également testé comme réponse du middleware.
- **404** : route inconnue et catalogue (ressource absente ou non visible); enveloppe `NOT_FOUND` vérifiée.
- **405** : méthode incorrecte sur santé; enveloppe commune vérifiée.
- **422** : validation query catalogue et endpoint temporaire de validation; enveloppe `VALIDATION_ERROR` et absence d'écho de la valeur soumise vérifiées.
- **500** : exception inattendue et défaillance du repository mock; message public générique, détails privés et secret non divulgués.
- **201** : non applicable aux routes réellement disponibles, car aucune route POST métier n'est enregistrée.

Les routes catalogue sont publiques et leur accès sans authentification est testé. Les tests 401/403 génériques ne démontrent pas les règles par rôle d'une API protégée; aucun endpoint protégé n'est livré sur `yasmin`, donc cette vérification n'est pas applicable au lot exécuté et reste explicitement prévue pour l'incrément où ces routes seront disponibles.

## Divergences et dépendances d'équipe

- Le catalogue local utilise `/api/v1/catalogue/programmes`, un détail par `slug` et le filtre `niveau`. Le contrat SA-5 mentionne `/api/v1/formations`, un identifiant et `cycle`; le contrat de routes définitif reste à confirmer avec Roua/Tasnime/Amina. Aucune convention n'a été changée ici.
- La référence candidate SA-21 est le snapshot `origin/feature/SA-21-catalogue-consultation` au commit `1be54c7dd5df0e259f06ad75fcec614cb3193516`, sans confirmation officielle de Roua.
- Le repository catalogue reste un mock JSON. L'intégration au schéma SA-12/PostgreSQL et la vérification des établissements réellement actifs ne sont pas couvertes.
- Les API d'authentification et permissions, de gestion SA-20, de dossiers, QCM, rendez-vous, conversations et outils internes ne sont pas enregistrées sur `yasmin`. Leurs scénarios sont préparés dans le plan de tests et seront exécutés lors de leur livraison, comme demandé par le principe officiel progressif. Leurs réponses 201, erreurs métier 400, 401/403 réels, validations et cas limites ne sont donc pas présentées comme testées dans cet incrément.
- Les formats communs, les IDs, la visibilité et les routes de ces API doivent suivre les contrats confirmés de SA-5, SA-12, SA-13, SA-20 et SA-21.

## Modifications de cette validation

- `tests/test_sa22_catalogue_contract.py` : ajout de CAT-18 pour le slug inexistant.
- `tests/CONTRACT_TEST_PLAN.md` : inventaire corrigé des routes présentes et séparation de la couverture exécutée des scénarios en attente.
- `QA_SA22_REPORT.md` : résultats exacts des exécutions ci-dessus et limites actualisées.

## Verdict

**SA-22 : DONE pour le lot actuellement livré, au sens de la fiche Sprint 1 qui demande une QA progressive.** Les routes disponibles ont été testées et documentées, les scénarios des API non encore livrées sont préparés sans être présentés comme exécutés, et les limites sont consignées. Après ajout des tests positifs SA-21, la suite backend compte 102 tests réussis, sans échec ni test ignoré. Les contrôles de rôles sur endpoints protégés et les autres API restent un travail QA futur, déclenché par leurs livraisons; ils ne sont pas revendiqués comme validés ici. La référence SA-21 et certaines conventions partagées doivent encore être confirmées pour l'intégration d'équipe. Aucune intégration PostgreSQL n'a été testée dans cette exécution.
