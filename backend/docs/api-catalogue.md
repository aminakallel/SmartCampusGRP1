# API de consultation du catalogue (SA-21)

Lecture seule, publique. Ne renvoie que les formations publiées.
La gestion du catalogue (créer, modifier, supprimer) relève de SA-20.
Les données viennent provisoirement de `app/catalogue_consultation/data/programmes.json`
(sources : iit.tn et isb.tn). Durées, conditions d'accès et débouchés restent à compléter.

## GET /api/catalogue/programmes

Paramètres, tous facultatifs :

| Paramètre | Valeurs | Rôle |
|---|---|---|
| `etablissement` | `IIT` ou `ISB` | Filtrer par établissement |
| `niveau` | `Licence`, `Préparatoire`, `Ingénierie`, `Master`, `Architecture` | Filtrer par niveau |
| `q` | 2 à 100 caractères | Recherche texte, sans accents ni majuscules (nom, description, mots-clés) |

Exemple de requête : `GET /api/catalogue/programmes?etablissement=ISB&niveau=Master&q=business`

Exemple de réponse 200 (extrait) :

```json
[
  {
    "id": "isb-master-in-business-administration-mba-eng",
    "slug": "isb-master-in-business-administration-mba-eng",
    "nom": "Master in Business Administration (MBA) (ENG)",
    "etablissement": "ISB",
    "niveau": "Master",
    "duree": "À renseigner",
    "description": "Master en administration des affaires (MBA), enseigné en anglais.",
    "prerequis": [],
    "debouches": [],
    "motsCles": ["MBA", "master", "business administration", "anglais"],
    "lien": "https://isb.tn/program-mba/"
  }
]
```

## GET /api/catalogue/programmes/{slug}

Réponse 200 : une formation, même format que ci-dessus.
Réponse 404 : `{"detail": "Formation introuvable."}`

## Erreurs

| Code | Cas |
|---|---|
| 422 | Paramètre invalide (par exemple `etablissement=XYZ`, ou `q` de moins de 2 caractères) |
| 404 | Formation introuvable ou non publiée |

## Évolution

Quand les tables du catalogue (SA-12) existeront, remplacer `MockCatalogueRepository` par un dépôt SQL
qui garde les mêmes méthodes `find_all` et `find_by_slug`. Les routes et les tests ne changent pas.
