# SmartCampus AI â€” Contrat d'Interface API & RÃ¨gles d'AccÃ¨s (TÃ¢che SA-5)

* **TÃ¢che Jira :** SA-5 â€” Concevoir les API et les rÃ¨gles d'accÃ¨s
* **Responsable :** Amina Kallel
* **Collaborateurs :** Tasnime (SA-4/SA-28 : Architecture & Auth), Manar (SA-3 : Processus mÃ©tiers), Roua (SA-8 : Frontend), Yasmine (SA-7/SA-22 : Backend & QA)
* **Base URL :** `/api/v1`

---

## 1. Conventions GÃ©nÃ©rales & SÃ©curitÃ©

* **Format d'Ã©change :** `application/json` (et `text/event-stream` pour le streaming SSE du chat).
* **MÃ©canismes d'authentification :**
  * **Utilisateurs (`candidat`, `admin`) :** Header `Authorization: Bearer <JWT_TOKEN>`
  * **Visiteur (`visiteur`) :** Header `X-Session-ID: <UUID_v4>` (identifiant de session anonyme temporaire)
  * **Formulaire externe (Webhook) :** Header `X-Webhook-Secret: <SHARED_SECRET>` vÃ©rifiÃ© via variable d'environnement
  * **Service Agents (Interne) :** Header `X-Internal-API-Key: <INTERNAL_KEY>` pour l'appel des outils Backend

### Format d'erreur standardisÃ©
Toutes les erreurs retournent une structure JSON uniforme avec le code HTTP appropriÃ© (`400`, `401`, `403`, `404`, `422`, `500`) :

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "AccÃ¨s refusÃ©",
    "details": {}
  }
}
```

---

## 2. Matrice des RÃ´les & RÃ¨gles d'AccÃ¨s (RBAC)

| RÃ´le technique | Acteur / Composant | PÃ©rimÃ¨tre d'autorisation |
| :--- | :--- | :--- |
| **`visiteur`** | Futur Ã©tudiant sans compte | Lecture publique du catalogue, chat anonyme via `session_id`, inscription et connexion. |
| **`candidat`** | Ã‰tudiant authentifiÃ© (JWT) | PÃ©rimÃ¨tre visiteur + gestion de son profil, rattachement de session, passage/reprise de son QCM, consultation de **son** dossier et de **ses** rendez-vous, rÃ©ponse aux propositions de crÃ©neaux. |
| **`admin`** | Administrateur & Direction | AccÃ¨s complet : CRUD formations/QCM/utilisateurs, lecture de tous les dossiers, **rÃ©sumÃ©s IA**, historiques complets de conversation, dÃ©cision sur dossier (`accepte`, `refuse`, `complement_demande`), confirmation des crÃ©neaux d'entretien. |
| **`system_webhook`** | Formulaire externe | Uniquement `POST /api/v1/preinscriptions/webhook`. |
| **`internal_agent`** | Service LangGraph (interne) | Uniquement les endpoints `/api/v1/internal/tools/*` (lecture/Ã©criture mÃ©tier, **aucun droit de dÃ©cision officielle**). |

### RÃ¨gles de sÃ©curitÃ© transverses
1. **Isolation des donnÃ©es (Ownership) :** Un `candidat` ne peut accÃ©der qu'aux ressources liÃ©es Ã  son propre identifiant (`candidat_id == current_user.id`). Toute tentative sur un autre ID renvoie `403 FORBIDDEN`.
2. **SÃ©paration Historique / RÃ©sumÃ© IA :** L'historique brut (`conversations`) et le rÃ©sumÃ© structurÃ© (`dossier.resume_ia`) sont deux ressources distinctes rÃ©servÃ©es Ã  l'`admin`.
3. **Human-in-the-loop :** Aucune route accessible aux agents ne permet de valider/refuser un dossier ni d'envoyer un crÃ©neau d'entretien au candidat sans confirmation prÃ©alable de l'`admin`.

---

## 3. Catalogue des Endpoints API (`/api/v1`)

### A. Authentification & Sessions (`/auth`)

| MÃ©thode | Route | RÃ´les autorisÃ©s | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/register` | `visiteur` | CrÃ©ation compte candidat + rattachement optionnel d'une session invitÃ©e. |
| `POST` | `/auth/login` | `visiteur` | Authentification et Ã©mission du token JWT. |
| `GET` | `/auth/me` | `candidat`, `admin` | RÃ©cupÃ©ration des informations de l'utilisateur connectÃ© et de son rÃ´le. |

**Validations & Exemples (`POST /auth/register`) :**
* **Validations :** `email` (format valide, unique), `password` (min. 8 caractÃ¨res), `nom` & `prenom` (2 Ã  50 caractÃ¨res), `session_id` (optionnel, format UUID v4).
* **RequÃªte :**
  ```json
  {
    "email": "amine.benali@example.tn",
    "password": "Password123!",
    "nom": "Ben Ali",
    "prenom": "Amine",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }
  ```
* **RÃ©ponse (`201 Created`) :**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1Ni...",
    "token_type": "bearer",
    "user": {
      "id": "usr_98a7b6",
      "email": "amine.benali@example.tn",
      "role": "candidat"
    },
    "conversation_rattachee": true
  }
  ```

---

### B. Conversation & Orientation IA (`/chat`)

| MÃ©thode | Route | RÃ´les autorisÃ©s | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/chat` | `visiteur`, `candidat` | Envoi d'un message (FR, tunisien, arabizi) et rÃ©ception en streaming SSE ou JSON. |
| `GET` | `/chat/historique` | `visiteur`, `candidat` | RÃ©cupÃ©ration des messages de la session active (`X-Session-ID` ou JWT). |
| `POST` | `/chat/rattacher` | `candidat` | Rattache manuellement un `session_id` anonyme au compte connectÃ©. |

**Validations & Exemples (`POST /chat`) :**
* **Validations :** `message` (requis, 1 Ã  2000 caractÃ¨res), `langue_detectee` (optionnel : `fr`, `tn`, `arabizi`), `session_id` (requis si rÃ´le = `visiteur`).
* **RequÃªte :**
  ```json
  {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Aslema, nheb naamel gÃ©nie logiciel ama ma naarech ken nemchi prÃ©pa wala licence"
  }
  ```
* **RÃ©ponse (`200 OK` - mode JSON ou chunk final SSE) :**
  ```json
  {
    "conversation_id": "conv_102",
    "reponse": "Marhba bik ! Pour le gÃ©nie logiciel Ã  l'IIT, tu as deux voies...",
    "langue": "arabizi",
    "sources_rag": [
      { "document": "Brochure_IIT_2026.pdf", "section": "Cycle IngÃ©nieur Informatique" }
    ],
    "profil_complet": false,
    "champs_manquants": ["niveau_scolaire", "moyenne_generale"]
  }
  ```

---

### C. Catalogue des Formations (`/formations`)

| MÃ©thode | Route | RÃ´les autorisÃ©s | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/formations` | `visiteur`, `candidat`, `admin` | Liste des formations (filtres : `?etablissement=IIT|ISB&cycle=licence|prepa|ingenierie`). |
| `GET` | `/formations/{id}` | `visiteur`, `candidat`, `admin` | DÃ©tail complet d'une formation (prÃ©requis, durÃ©e, dÃ©bouchÃ©s). |
| `POST` | `/formations` | `admin` | CrÃ©ation d'une formation et dÃ©clenchement de l'indexation RAG. |
| `PUT` | `/formations/{id}` | `admin` | Modification d'une formation. |
| `DELETE` | `/formations/{id}` | `admin` | Suppression d'une formation. |

---

### D. Profil Candidat (`/candidats`)

| MÃ©thode | Route | RÃ´les autorisÃ©s | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/candidats/{id}/profil` | `candidat` (soi-mÃªme), `admin` | Consulter le profil acadÃ©mique et les prÃ©fÃ©rences. |
| `PUT` | `/candidats/{id}/profil` | `candidat` (soi-mÃªme) | ComplÃ©ter/mettre Ã  jour le profil (dÃ©clenche la vÃ©rification de complÃ©tude). |
| `GET` | `/candidats/{id}/recommandations` | `candidat` (soi-mÃªme), `admin` | RÃ©cupÃ©rer la shortlist des formations recommandÃ©es et leurs justifications. |
| `GET` | `/candidats/{id}/conversations` | `admin` | Consulter l'historique complet des conversations d'un candidat. |

**Validations (`PUT /candidats/{id}/profil`) :**
* `niveau_scolaire` : enum (`bac`, `licence_1`, `licence_2`, `licence_3`, `prepa`, `autre`)
* `specialite_origine` : string (ex: `"MathÃ©matiques"`, `"Sciences ExpÃ©rimentales"`, `"Informatique"`)
* `interets` : array de strings (min. 1 Ã©lÃ©ment pour valider la complÃ©tude)
* `objectifs_professionnels` : string (10 Ã  500 caractÃ¨res)

---

### E. PrÃ©inscription & Dossiers (`/preinscriptions` & `/dossiers`)

| MÃ©thode | Route | RÃ´les autorisÃ©s | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/preinscriptions/lien` | `candidat` | GÃ©nÃ¨re l'URL du formulaire externe prÃ©-remplie avec `candidat_id`. |
| `POST` | `/preinscriptions/webhook` | `system_webhook` | ReÃ§oit la soumission externe $\rightarrow$ assemble le dossier + gÃ©nÃ¨re le rÃ©sumÃ© IA + initie l'entretien. |
| `GET` | `/candidats/{id}/dossier` | `candidat` (soi-mÃªme), `admin` | Consulte l'Ã©tat du dossier (Note : le champ `resume_ia` est **masquÃ©** si rÃ´le = `candidat`). |
| `GET` | `/dossiers` | `admin` | Liste paginÃ©e de tous les dossiers (filtre `?statut=soumis|complement_demande|accepte|refuse`). |
| `GET` | `/dossiers/{id}` | `admin` | DÃ©tail complet du dossier incluant les donnÃ©es administratives, le **rÃ©sumÃ© IA** et le score QCM. |
| `PATCH` | `/dossiers/{id}/statut` | `admin` | DÃ©cision humaine : `accepte`, `refuse` ou `complement_demande` (avec motif). |
| `POST` | `/dossiers/{id}/complements` | `candidat` (propriÃ©taire) | Soumission des piÃ¨ces/informations demandÃ©es par l'admin. |

**Exemples (`POST /preinscriptions/webhook` & `PATCH /dossiers/{id}/statut`) :**
* **RequÃªte Webhook (`POST /preinscriptions/webhook`) :**
  ```json
  {
    "candidat_id": "usr_98a7b6",
    "formation_choisie_id": "form_ing_info",
    "donnees_administratives": {
      "cin_ou_passeport": "11223344",
      "telephone": "+21622000111",
      "lycee_ou_universite": "LycÃ©e Pilote Sfax"
    },
    "soumis_le": "2026-11-22T12:30:00Z"
  }
  ```
* **RequÃªte DÃ©cision Admin (`PATCH /dossiers/{id}/statut`) :**
  ```json
  {
    "statut": "complement_demande",
    "commentaire": "Merci de prÃ©ciser votre relevÃ© de notes du 2Ã¨me trimestre."
  }
  ```

---

### F. QCM PersonnalisÃ© (`/qcm`)

| MÃ©thode | Route | RÃ´les autorisÃ©s | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/candidats/{id}/qcm` | `candidat` (soi-mÃªme) | RÃ©cupÃ¨re le QCM gÃ©nÃ©rÃ© et la derniÃ¨re progression sauvegardÃ©e. |
| `POST` | `/qcm/{id}/progression` | `candidat` (propriÃ©taire) | Sauvegarde partielle des rÃ©ponses (permet la reprise aprÃ¨s interruption). |
| `POST` | `/qcm/{id}/soumettre` | `candidat` (propriÃ©taire) | ClÃ´ture dÃ©finitive du QCM, calcul du score et synthÃ¨se des acquis. |
| `GET` | `/dossiers/{id}/qcm-resultats` | `admin` | Consulte les questions gÃ©nÃ©rÃ©es, rÃ©ponses du candidat et analyse des acquis. |

**Validations & Exemples (`POST /qcm/{id}/progression`) :**
* **Validations :** Le QCM ne doit pas dÃ©jÃ  Ãªtre au statut `termine`. `question_index` $\ge 0$.
* **RequÃªte :**
  ```json
  {
    "question_index": 3,
    "reponses": [
      { "question_id": "q_1", "choix_id": "opt_b" },
      { "question_id": "q_2", "choix_id": "opt_a" }
    ]
  }
  ```
* **RÃ©ponse (`200 OK`) :**
  ```json
  {
    "qcm_id": "qcm_445",
    "statut": "en_cours",
    "progression_pourcentage": 40,
    "sauvegarde_le": "2026-11-22T12:40:00Z"
  }
  ```

---

### G. Organisation des Entretiens (`/rendez-vous`)

| MÃ©thode | Route | RÃ´les autorisÃ©s | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/rendez-vous` | `candidat` (les siens), `admin` (tous) | Liste des rendez-vous et de leur statut (`propose`, `confirme`, `indisponible`). |
| `POST` | `/rendez-vous/{id}/confirmer` | `admin` | L'admin sÃ©lectionne et confirme un crÃ©neau avant envoi au candidat. |
| `POST` | `/rendez-vous/{id}/reponse-candidat` | `candidat` (propriÃ©taire) | Le candidat accepte (`confirme`) ou signale son indisponibilitÃ© (`indisponible`). |

**Validations & Exemples (`POST /rendez-vous/{id}/reponse-candidat`) :**
* **Validations :** `decision` $\in$ `["confirme", "indisponible"]`. Si `"indisponible"`, `motif_ou_disponibilites` est obligatoire (min. 5 caractÃ¨res) afin d'alerter l'admin.
* **RequÃªte :**
  ```json
  {
    "decision": "indisponible",
    "motif_ou_disponibilites": "Examen le matin, disponible l'aprÃ¨s-midi Ã  partir de 14h."
  }
  ```
* **RÃ©ponse (`200 OK`) :**
  ```json
  {
    "rendez_vous_id": "rdv_778",
    "statut": "indisponible",
    "notification_admin_envoyee": true
  }
  ```

---

## 4. Endpoints Internes (Outils exposÃ©s aux Agents LangGraph)

ConformÃ©ment Ã  la rÃ¨gle d'architecture nÂ°1 (les agents n'accÃ¨dent jamais directement Ã  PostgreSQL ou SMTP), le Backend expose ces routes protÃ©gÃ©es par `X-Internal-API-Key` :

* `POST /api/v1/internal/tools/save-message` : Persiste un tour de conversation.
* `GET /api/v1/internal/tools/get-profile/{candidat_id}` : Lit le profil pour vÃ©rifier sa complÃ©tude.
* `POST /api/v1/internal/tools/save-recommendations` : Enregistre la shortlist gÃ©nÃ©rÃ©e.
* `POST /api/v1/internal/tools/save-dossier-summary` : Enregistre le rÃ©sumÃ© structurÃ© IA du dossier.
* `POST /api/v1/internal/tools/propose-slots` : Calcule et propose des crÃ©neaux libres Ã  l'administrateur (sans les envoyer au candidat).
* `POST /api/v1/internal/tools/send-email` : DÃ©clenche l'envoi d'un email (uniquement aprÃ¨s validation/action autorisÃ©e).
