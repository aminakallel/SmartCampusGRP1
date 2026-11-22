# Rapport QA — SA-18, préparation du seed initial

**État au : 22 novembre 2026**  
**Verdict : PARTIAL** — préparation et validation hors base réalisées; seed métier PostgreSQL non terminé.

## Objectif et périmètre

SA-18 est la tâche de préparation du **seed initial des données de démonstration SmartCampus AI**. La répartition Sprint 1 n'étant pas présente dans le checkout examiné, ce rapport reprend l'intitulé et l'objectif communiqués dans le contexte du projet. Les critères d'acceptation Jira exacts n'ont pas pu être vérifiés dans ce dépôt.

Le travail réalisé prépare des données fictives et leur plan de chargement. Il ne constitue pas un chargement dans les tables métier.

## Fichiers SA-18 présents

| Fichier | Rôle / état |
| --- | --- |
| `seed_data/initial_data.json` | Fixture métier fictive et provisoire, conçue selon SA-12 et SA-13. |
| `scripts/validate_initial_data.py` | Validation structurelle, des champs et des références croisées; aucune connexion à la base. |
| `scripts/plan_initial_data.py` | Plan descriptif des écritures, dépendances et blocages; n'émet ni SQL ni identifiants SERIAL. Toujours non exécutable. |
| `tests/test_initial_data.py` | Tests de la fixture, de ses références, de ses contraintes et des doublons. |
| `tests/test_initial_data_plan.py` | Tests du plan, des clés de résolution, des blocages et du contrôle de conflit d'intérêt avec un faux repository. |
| `seed_data/demo_records.json`, `scripts/seed_demo.py`, `tests/test_seed_demo.py` | Seed de démonstration de staging préexistant; il reste distinct du seed métier SA-18 et n'a pas été remplacé. |

Le rapport lui-même est le nouveau livrable `QA_SA18_REPORT.md`.

## Contenu de la fixture et couverture SA-12

`initial_data.json` contient deux établissements fictifs (IIT et ISB), deux formations, deux critères d'admission, un candidat et son profil, deux résultats scolaires, deux intérêts et deux associations profil-intérêt. Les valeurs d'établissement, de formation et d'admission sont explicitement provisoires. Aucun mot de passe ou hash n'est inventé.

Les quatre tables du catalogue SA-12 sont prises en compte :

| Table SA-12 | Fixture actuelle | Référence / traitement prévu |
| --- | --- | --- |
| `etablissements` | 2 enregistrements | Identité recherchée par `code`; `id` SERIAL laissé à la base. |
| `formations_parcours` | 2 enregistrements | Établissement résolu par `etablissement_code_ref` vers `etablissements.code`; `id` SERIAL laissé à la base. |
| `criteres_admission` | 2 enregistrements | Formation résolue par `parcours_code_ref` vers `formations_parcours.code_parcours`; `id` SERIAL laissé à la base. |
| `documents_catalogue_rag` | Collection vide | Aucun contenu, source ou embedding n'a été fabriqué. La structure et la résolution de référence sont validées par tests avec un enregistrement synthétique, sans l'ajouter à la fixture livrée. |

Les UUID des entités SA-13 sont présents dans la fixture. Les liens profil/utilisateur et profil/résultats/intérêts sont vérifiés par le validateur. L'ordre déclaré place les parents avant les entités qui en dépendent.

## Validateur et planificateur

Le validateur vérifie les formes des champs, les valeurs provisoires, les plages numériques, l'absence de propriétés non prévues, les références aux établissements/formations/utilisateur/profil/intérêts et les doublons présents dans la fixture. Il rejette notamment les identifiants SERIAL fournis dans les données du catalogue et les champs de mot de passe/hash.

Le planificateur décrit 14 entrées de lignes à préparer pour les collections non vides. Il indique les clés de conflit et les colonnes SERIAL générées, ainsi que les résolutions de clés étrangères. Il marque le plan `executable=False`. Pour `criteres_admission` et `documents_catalogue_rag`, il n'invente aucune clé UNIQUE et signale qu'une stratégie d'idempotence doit être décidée. Une vérification en lecture seule du libellé d'un intérêt peut être exercée avec un faux repository; ce n'est pas un chargeur ni un accès PostgreSQL.

## Tests et vérifications réellement exécutés

Commande exécutée depuis `backend` avec le virtualenv disponible dans le backend voisin :

```powershell
& 'C:\Users\dhieb\Downloads\ia génerative\backend\.venv\Scripts\python.exe' -m pytest -v tests\test_initial_data.py tests\test_initial_data_plan.py
```

**Résultat : 40 réussis, 0 échoué, en 0,77 s** (Python 3.12.3, pytest 8.3.5).

Les tests couvrent notamment :

- la cohérence des données fictives, de la moyenne pondérée et des intérêts liés au programme IIT;
- l'ordre de dépendance, les références invalides et l'absence d'identifiants SERIAL dans les lignes de catalogue;
- les champs requis SA-12, les critères, la structure RAG et la dimension d'embedding;
- l'absence de secrets de mot de passe/hash dans la fixture;
- les doublons de code établissement, code formation, clé métier de résultat `(profil_id, matiere, periode)`, libellé d'intérêt, association `(profil_id, interet_id)` et `seed_key`;
- les clés de résolution et le caractère descriptif/non exécutable du plan;
- le conflit d'un libellé d'intérêt déjà associé à un autre UUID, ainsi que les cas sans conflit, via un faux repository.

Ces vérifications sont **hors base** : elles n'ont pas ouvert de connexion, exécuté de SQL, lancé de seed ou modifié des données PostgreSQL. Aucun test n'établit la persistance effective ni le comportement des contraintes de la future migration SA-12.

## Limites et dépendances restantes

1. **Migration SA-12 absente/non validée dans le checkout** : impossible d'insérer ou de vérifier les quatre tables catalogue en PostgreSQL.
2. **Idempotence des critères et documents RAG** : SA-12 ne fournit pas de clé UNIQUE confirmée pour ces enregistrements; l'équipe doit convenir d'une stratégie avant un seed relançable.
3. **Compte candidat** : `utilisateur.mot_de_passe_hash` est requis par SA-13; la fixture et le plan bloquent cet enregistrement tant qu'un fournisseur de hash approuvé n'est pas disponible.
4. **Données RAG réelles** : la collection est vide en attente de sources approuvées et, si requis, de leur traitement/embeddings.
5. **Intégration et persistance** : aucun chargeur métier PostgreSQL n'est fourni ou exécuté. La validation du schéma, des transactions, des FK et de l'idempotence en base reste à effectuer dans un environnement isolé après réception de SA-12.

## Verdict

**Préparation hors base : terminée pour les fixtures présentes et leur validation automatisée.** Les tests ciblés passent et le plan respecte les identifiants SERIAL générés par la base ainsi que l'absence de clé UNIQUE inventée pour critères/RAG.

**Seed métier PostgreSQL : non terminé. SA-18 reste PARTIAL.** Il ne doit pas être annoncé comme une insertion métier terminée ou persistée. Pour le faire évoluer vers DONE, il faudra disposer de la migration SA-12 validée, décider l'idempotence critères/RAG, obtenir le mécanisme de hash approuvé, fournir les contenus RAG attendus, puis ajouter et exécuter les tests d'intégration/persistance/idempotence dans une base de test isolée.
