# API de consultation du catalogue — SA-21

## État et traçabilité

Cette implémentation sur `yasmin` reprend le modèle de consultation et le jeu JSON du snapshot candidat `origin/feature/SA-21-catalogue-consultation` au commit `1be54c7dd5df0e259f06ad75fcec614cb3193516`. La référence n'est pas une confirmation officielle de Roua. Les adaptations locales sont : préfixe versionné, enveloppe d'erreur SA-5 commune et statuts alignés sur les valeurs SA-12 (`BROUILLON`, `PUBLIE`, `ARCHIVE`).

Le dépôt est actuellement un adaptateur JSON sans SQL. Il devra être remplacé par un repository SA-12 après disponibilité et validation de sa migration. Le jeu de données provient du snapshot candidat et certaines informations y sont encore à renseigner ; ne pas le considérer comme un catalogue officiel validé.

## Routes implémentées

### `GET /api/v1/catalogue/programmes`

Renvoie une liste de `ProgrammePublic`. Paramètres facultatifs :

- `etablissement`: `IIT` ou `ISB`.
- `niveau`: `Licence`, `Préparatoire`, `Ingénierie`, `Master` ou `Architecture`.
- `q`: recherche sur le nom, la description et les mots-clés. Les espaces en début et fin sont retirés avant validation; une valeur vide après ce retrait est rejetée en HTTP 422. La longueur normalisée doit être comprise entre 2 et 100 caractères. La recherche est insensible à la casse et aux accents. Le paramètre reste facultatif lorsqu'il est omis.

La visibilité publique est limitée aux statuts `PUBLIE` et aux établissements considérés actifs. L'adaptateur de démonstration suppose provisoirement IIT et ISB actifs; le repository PostgreSQL devra lire `etablissements.est_actif`.

### `GET /api/v1/catalogue/programmes/{slug}`

Renvoie le même schéma public pour une formation visible. Un slug absent, brouillon, archivé ou rattaché à un établissement inactif répond 404.

### Erreurs

Les erreurs HTTP utilisent l'enveloppe commune :

```json
{"error":{"code":"NOT_FOUND","message":"Formation introuvable.","details":{}}}
```

Les paramètres invalides répondent 422 avec `VALIDATION_ERROR` et les détails de validation, sans inclure les valeurs saisies.

## Contrats à harmoniser avant intégration commune

- Le contrat SA-5 décrit `/api/v1/formations` et un détail par identifiant; Tasnime a aussi des routes de gestion sous `/api/v1/formations`. La présente API conserve un espace distinct et un détail par slug pour éviter la collision et préserver SA-21. Roua et Tasnime doivent confirmer le chemin final et le mapping slug/ID SERIAL.
- Le filtre candidat s'appelle `niveau`; le contrat partagé mentionne `cycle`. Aucune conversion entre les deux n'est inventée ici.
- Les valeurs affichées du niveau et les données académiques du fichier restent à confirmer auprès de Tasnime.
- La confirmation de Roua sur le snapshot source et la conformité des données restent attendues.

## Exécution

Depuis `backend/` :

```powershell
python -m uvicorn app.main:app --reload
```

Documentation interactive : `http://127.0.0.1:8000/docs`.
