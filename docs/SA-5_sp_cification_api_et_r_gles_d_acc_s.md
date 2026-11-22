# SmartCampus AI — Contrat d'Interface API & Règles d'Accès (Tâche SA-5)

* **Tâche Jira :** SA-5 — Concevoir les API et les règles d'accès
* **Responsable :** Amina Kallel
* **Collaborateurs :** Tasnime (SA-4/SA-28 : Architecture & Auth), Manar (SA-3 : Processus métiers), Roua (SA-8 : Frontend), Yasmine (SA-7/SA-22 : Backend & QA)
* **Base URL :** `/api/v1`

---

## 1. Conventions Générales & Sécurité

* **Format d'échange :** `application/json` (et `text/event-stream` pour le streaming SSE du chat).
* **Mécanismes d'authentification :**
  * **Utilisateurs (`candidat`, `admin`) :** Header `Authorization: Bearer <JWT_TOKEN>`
  * **Visiteur (`visiteur`) :** Header `X-Session-ID: <UUID_v4>` (identifiant de session anonyme temporaire)
  * **Formulaire externe (Webhook) :** Header `X-Webhook-Secret: <SHARED_SECRET>` vérifié via variable d'environnement
  * **Service Agents (Interne) :** Header `X-Internal-API-Key: <INTERNAL_KEY>` pour l'appel des outils Backend

### Format d'erreur standardisé
Toutes les erreurs retournent une structure JSON uniforme avec le code HTTP approprié (`400`, `401`, `403`, `404`, `422`, `500`) :

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Accès refusé",
    "details": {}
  }
}
```

---

## 2. Matrice des Rôles & Règles d'Accès (RBAC)

| Rôle technique | Acteur / Composant | Périmètre d'autorisation |
| :--- | :--- | :--- |
| **`visiteur`** | Futur étudiant sans compte | Lecture publique du catalogue, chat anonyme via `session_id`, inscription et connexion. |
| **`candidat`** | Étudiant authentifié (JWT) | Périmètre visiteur + gestion de son profil, rattachement de session, passage/reprise de son QCM, consultation de **son** dossier et de **ses** rendez-vous, réponse aux propositions de créneaux. |
| **`admin`** | Administrateur & Direction | Accès complet : CRUD formations/QCM/utilisateurs, lecture de tous les dossiers, **résumés IA**, historiques complets de conversation, décision sur dossier (`accepte`, `refuse`, `complement_demande`), confirmation des créneaux d'entretien. |
| **`system_webhook`** | Formulaire externe | Uniquement `POST /api/v1/preinscriptions/webhook`. |
| **`internal_agent`** | Service LangGraph (interne) | Uniquement les endpoints `/api/v1/internal/tools/*` (lecture/écriture métier, **aucun droit de décision officielle**). |

### Règles de sécurité transverses
1. **Isolation des données (Ownership) :** Un `candidat` ne peut accéder qu'aux ressources liées à son propre identifiant (`candidat_id == current_user.id`). Toute tentative sur un autre ID renvoie `403 FORBIDDEN`.
2. **Séparation Historique / Résumé IA :** L'historique brut (`conversations`) et le résumé structuré (`dossier.resume_ia`) sont deux ressources distinctes réservées à l'`admin`.
3. **Human-in-the-loop :** Aucune route accessible aux agents ne permet de valider/refuser un dossier ni d'envoyer un créneau d'entretien au candidat sans confirmation préalable de l'`admin`.

---

## 3. Catalogue des Endpoints API (`/api/v1`)

### A. Authentification & Sessions (`/auth`)

| Méthode | Route | Rôles autorisés | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/register` | `visiteur` | Création compte candidat + rattachement optionnel d'une session invitée. |
| `POST` | `/auth/login` | `visiteur` | Authentification et émission du token JWT. |
| `GET` | `/auth/me` | `candidat`, `admin` | Récupération des informations de l'utilisateur connecté et de son rôle. |

**Validations & Exemples (`POST /auth/register`) :**
* **Validations :** `email` (format valide, unique), `password` (min. 8 caractères), `nom` & `prenom` (2 à 50 caractères), `session_id` (optionnel, format UUID v4).
* **Requête :**
  ```json
  {
    "email": "amine.benali@example.tn",
    "password": "Password123!",
    "nom": "Ben Ali",
    "prenom": "Amine",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }
  ```
* **Réponse (`201 Created`) :**
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

| Méthode | Route | Rôles autorisés | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/chat` | `visiteur`, `candidat` | Envoi d'un message (FR, tunisien, arabizi) et réception en streaming SSE ou JSON. |
| `GET` | `/chat/historique` | `visiteur`, `candidat` | Récupération des messages de la session active (`X-Session-ID` ou JWT). |
| `POST` | `/chat/rattacher` | `candidat` | Rattache manuellement un `session_id` anonyme au compte connecté. |

**Validations & Exemples (`POST /chat`) :**
* **Validations :** `message` (requis, 1 à 2000 caractères), `langue_detectee` (optionnel : `fr`, `tn`, `arabizi`), `session_id` (requis si rôle = `visiteur`).
* **Requête :**
  ```json
  {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Aslema, nheb naamel génie logiciel ama ma naarech ken nemchi prépa wala licence"
  }
  ```
* **Réponse (`200 OK` - mode JSON ou chunk final SSE) :**
  ```json
  {
    "conversation_id": "conv_102",
    "reponse": "Marhba bik ! Pour le génie logiciel à l'IIT, tu as deux voies...",
    "langue": "arabizi",
    "sources_rag": [
      { "document": "Brochure_IIT_2026.pdf", "section": "Cycle Ingénieur Informatique" }
    ],
    "profil_complet": false,
    "champs_manquants": ["niveau_scolaire", "moyenne_generale"]
  }
  ```

---

### C. Catalogue des Formations (`/formations`)

| Méthode | Route | Rôles autorisés | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/formations` | `visiteur`, `candidat`, `admin` | Liste des formations (filtres : `?etablissement=IIT|ISB&cycle=licence|prepa|ingenierie`). |
| `GET` | `/formations/{id}` | `visiteur`, `candidat`, `admin` | Détail complet d'une formation (prérequis, durée, débouchés). |
| `POST` | `/formations` | `admin` | Création d'une formation et déclenchement de l'indexation RAG. |
| `PUT` | `/formations/{id}` | `admin` | Modification d'une formation. |
| `DELETE` | `/formations/{id}` | `admin` | Suppression d'une formation. |

---

### D. Profil Candidat (`/candidats`)

| Méthode | Route | Rôles autorisés | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/candidats/{id}/profil` | `candidat` (soi-même), `admin` | Consulter le profil académique et les préférences. |
| `PUT` | `/candidats/{id}/profil` | `candidat` (soi-même) | Compléter/mettre à jour le profil (déclenche la vérification de complétude). |
| `GET` | `/candidats/{id}/recommandations` | `candidat` (soi-même), `admin` | Récupérer la shortlist des formations recommandées et leurs justifications. |
| `GET` | `/candidats/{id}/conversations` | `admin` | Consulter l'historique complet des conversations d'un candidat. |

**Validations (`PUT /candidats/{id}/profil`) :**
* `niveau_scolaire` : enum (`bac`, `licence_1`, `licence_2`, `licence_3`, `prepa`, `autre`)
* `specialite_origine` : string (ex: `"Mathématiques"`, `"Sciences Expérimentales"`, `"Informatique"`)
* `interets` : array de strings (min. 1 élément pour valider la complétude)
* `objectifs_professionnels` : string (10 à 500 caractères)

---

### E. Préinscription & Dossiers (`/preinscriptions` & `/dossiers`)

| Méthode | Route | Rôles autorisés | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/preinscriptions/lien` | `candidat` | Génère l'URL du formulaire externe pré-remplie avec `candidat_id`. |
| `POST` | `/preinscriptions/webhook` | `system_webhook` | Reçoit la soumission externe $\rightarrow$ assemble le dossier + génère le résumé IA + initie l'entretien. |
| `GET` | `/candidats/{id}/dossier` | `candidat` (soi-même), `admin` | Consulte l'état du dossier (Note : le champ `resume_ia` est **masqué** si rôle = `candidat`). |
| `GET` | `/dossiers` | `admin` | Liste paginée de tous les dossiers (filtre `?statut=soumis|complement_demande|accepte|refuse`). |
| `GET` | `/dossiers/{id}` | `admin` | Détail complet du dossier incluant les données administratives, le **résumé IA** et le score QCM. |
| `PATCH` | `/dossiers/{id}/statut` | `admin` | Décision humaine : `accepte`, `refuse` ou `complement_demande` (avec motif). |
| `POST` | `/dossiers/{id}/complements` | `candidat` (propriétaire) | Soumission des pièces/informations demandées par l'admin. |

**Exemples (`POST /preinscriptions/webhook` & `PATCH /dossiers/{id}/statut`) :**
* **Requête Webhook (`POST /preinscriptions/webhook`) :**
  ```json
  {
    "candidat_id": "usr_98a7b6",
    "formation_choisie_id": "form_ing_info",
    "donnees_administratives": {
      "cin_ou_passeport": "11223344",
      "telephone": "+21622000111",
      "lycee_ou_universite": "Lycée Pilote Sfax"
    },
    "soumis_le": "2026-11-22T12:30:00Z"
  }
  ```
* **Requête Décision Admin (`PATCH /dossiers/{id}/statut`) :**
  ```json
  {
    "statut": "complement_demande",
    "commentaire": "Merci de préciser votre relevé de notes du 2ème trimestre."
  }
  ```

---

### F. QCM Personnalisé (`/qcm`)

| Méthode | Route | Rôles autorisés | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/candidats/{id}/qcm` | `candidat` (soi-même) | Récupère le QCM généré et la dernière progression sauvegardée. |
| `POST` | `/qcm/{id}/progression` | `candidat` (propriétaire) | Sauvegarde partielle des réponses (permet la reprise après interruption). |
| `POST` | `/qcm/{id}/soumettre` | `candidat` (propriétaire) | Clôture définitive du QCM, calcul du score et synthèse des acquis. |
| `GET` | `/dossiers/{id}/qcm-resultats` | `admin` | Consulte les questions générées, réponses du candidat et analyse des acquis. |

**Validations & Exemples (`POST /qcm/{id}/progression`) :**
* **Validations :** Le QCM ne doit pas déjà être au statut `termine`. `question_index` $\ge 0$.
* **Requête :**
  ```json
  {
    "question_index": 3,
    "reponses": [
      { "question_id": "q_1", "choix_id": "opt_b" },
      { "question_id": "q_2", "choix_id": "opt_a" }
    ]
  }
  ```
* **Réponse (`200 OK`) :**
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

| Méthode | Route | Rôles autorisés | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/rendez-vous` | `candidat` (les siens), `admin` (tous) | Liste des rendez-vous et de leur statut (`propose`, `confirme`, `indisponible`). |
| `POST` | `/rendez-vous/{id}/confirmer` | `admin` | L'admin sélectionne et confirme un créneau avant envoi au candidat. |
| `POST` | `/rendez-vous/{id}/reponse-candidat` | `candidat` (propriétaire) | Le candidat accepte (`confirme`) ou signale son indisponibilité (`indisponible`). |

**Validations & Exemples (`POST /rendez-vous/{id}/reponse-candidat`) :**
* **Validations :** `decision` $\in$ `["confirme", "indisponible"]`. Si `"indisponible"`, `motif_ou_disponibilites` est obligatoire (min. 5 caractères) afin d'alerter l'admin.
* **Requête :**
  ```json
  {
    "decision": "indisponible",
    "motif_ou_disponibilites": "Examen le matin, disponible l'après-midi à partir de 14h."
  }
  ```
* **Réponse (`200 OK`) :**
  ```json
  {
    "rendez_vous_id": "rdv_778",
    "statut": "indisponible",
    "notification_admin_envoyee": true
  }
  ```

---

## 4. Endpoints Internes (Outils exposés aux Agents LangGraph)

Conformément à la règle d'architecture n°1 (les agents n'accèdent jamais directement à PostgreSQL ou SMTP), le Backend expose ces routes protégées par `X-Internal-API-Key` :

* `POST /api/v1/internal/tools/save-message` : Persiste un tour de conversation.
* `GET /api/v1/internal/tools/get-profile/{candidat_id}` : Lit le profil pour vérifier sa complétude.
* `POST /api/v1/internal/tools/save-recommendations` : Enregistre la shortlist générée.
* `POST /api/v1/internal/tools/save-dossier-summary` : Enregistre le résumé structuré IA du dossier.
* `POST /api/v1/internal/tools/propose-slots` : Calcule et propose des créneaux libres à l'administrateur (sans les envoyer au candidat).
* `POST /api/v1/internal/tools/send-email` : Déclenche l'envoi d'un email (uniquement après validation/action autorisée).