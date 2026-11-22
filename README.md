# SmartCampus AI — Frontend

Interface de la plateforme agentique d'orientation universitaire **SmartCampus AI**.
Le site est centré sur le chat : l'accueil propose une conversation avec l'assistant
IA pour découvrir les formations de l'**IIT** et de l'**ISB**, puis se préinscrire sur
le site de la faculté. L'espace équipe (dashboard) permet de suivre les candidatures.

> Tâche SA-8 — Initialiser le Frontend (Next.js).

## Stack

- **Next.js 16** (App Router, Turbopack)
- **React 19** + **TypeScript**
- **Tailwind CSS 4**

## Prérequis

- **Node.js 20.9 ou supérieur** — vérifier avec `node -v`
- **npm** (fourni avec Node.js)

## Installation

```bash
npm install
```

## Lancement en développement

```bash
npm run dev
```

Puis ouvrir [http://localhost:3000](http://localhost:3000) dans le navigateur.
La page se met à jour automatiquement à chaque modification.

## Configuration de la connexion API

La connexion au backend est pilotée par variables d'environnement. Copier le fichier
d'exemple puis adapter si nécessaire :

```bash
copy .env.example .env.local
```

| Variable                         | Rôle                                                                | Valeur par défaut |
| -------------------------------- | ------------------------------------------------------------------- | ----------------- |
| `NEXT_PUBLIC_API_BASE_URL`       | URL de base du backend (ex. `http://localhost:8000`).               | vide              |
| `NEXT_PUBLIC_USE_MOCK_API`       | `"true"` pour forcer les données locales, `"false"` pour l'API.     | vide              |
| `NEXT_PUBLIC_PREINSCRIPTION_URL` | Lien externe du formulaire de préinscription de la faculté.         | vide              |

> Le bouton « Se préinscrire » est masqué tant que `NEXT_PUBLIC_PREINSCRIPTION_URL`
> est vide (aucun lien mort n'est affiché).

**Fonctionnement du mode mock :** tant que `NEXT_PUBLIC_API_BASE_URL` est vide,
l'application fonctionne **sans backend** grâce aux données de démonstration
(`lib/mock-data.ts`). Dès que l'URL est renseignée, les services appellent l'API réelle
(par exemple `GET {API_BASE_URL}/api/catalogue/programmes`).

> Les variables exposées au navigateur doivent obligatoirement être préfixées par
> `NEXT_PUBLIC_`, c'est pourquoi la variable `API_BASE_URL` est nommée
> `NEXT_PUBLIC_API_BASE_URL`.

## Structure du projet

```
app/                         Routes et pages (App Router)
  layout.tsx                 Layout racine (header + footer + chat + métadonnées)
  page.tsx                   Accueil (chat ouvert automatiquement)
  dashboard/                 Espace admissions (responsables)
  not-found.tsx              Page 404
components/
  site/                      Header et footer du site
  ui/                        Composants communs (Button, Card, Badge, Container...)
  chat/                      Chat, cartes de formations
lib/
  config.ts                  Configuration (API, préinscription, mode mock)
  api-client.ts              Client HTTP générique vers le backend
  services/catalogue.ts      Services de consultation du catalogue
  assistant.ts               Réponses simulées du chat (mode mock)
  mock-data.ts               Données de démonstration
  navigation.ts              Éléments de navigation
  cn.ts                      Utilitaire de classes CSS
types/                       Types métier partagés (Programme, ChatMessage...)
```

## Routes disponibles

| Route        | Description                                    |
| ------------ | ---------------------------------------------- |
| `/`          | Accueil — chat d'orientation (ouvert d'office) |
| `/dashboard` | Espace admissions (responsables)               |

La préinscription n'est plus une route interne : elle pointe vers le formulaire
externe de la faculté via `NEXT_PUBLIC_PREINSCRIPTION_URL`.

## Scripts

| Commande        | Description                                  |
| --------------- | -------------------------------------------- |
| `npm run dev`   | Démarre le serveur de développement           |
| `npm run build` | Compile l'application pour la production      |
| `npm start`     | Démarre le serveur de production              |
| `npm run lint`  | Analyse statique du code (ESLint)             |

## Notes

- Les réponses de l'assistant utilisent des **données mockées** (`lib/mock-data.ts`) :
  le modèle LLM (SA-36/SA-37), la mémoire conversationnelle (SA-26) et les API du
  catalogue (SA-21) seront connectés ultérieurement.
- Le chat remplace le catalogue : il répond avec les formations issues de
  `lib/mock-data.ts` et affiche des cartes dépliables dans le fil.
- L'interface est **responsive** et prend en charge le thème clair et sombre.
