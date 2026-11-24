# SA-38 — Cahier de Recette et Rapport QA Croisé du Dialogue (SmartCampus AI)

## 1. Objectif et Périmètre du Test
Vérifier le fonctionnement complet du parcours conversationnel (Frontend Next.js + Backend FastAPI + Mémoire + LLM `Qwen/Qwen2.5-7B-Instruct`) sur les scénarios clés : premier échange, collecte de profil, orientation IIT/ISB, suivi du contexte multi-tour, dialecte tunisien/Arabizi et gestion des erreurs[cite: 8, 9, 11].

---

## 2. Scénarios de Recette QA

| ID Test | Parcours / Scénario | Entrée utilisateur (Action) | Résultat attendu | Résultat obtenu | Statut (`OK` / `KO`) |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **QA-01** | **Premier échange (Session invitée)** | Un visiteur ouvre le chat sans compte et envoie : *"Bonjour, je veux des infos sur l'IIT."* | Création d'une session invitée (`session_id` UUID), accueil poli et demande d'informations sur le profil scolaire[cite: 7, 11]. | *À tester après intégration SA-25 / SA-36* | `À exécuter` |
| **QA-02** | **Questions de profil (Profil incomplet)** | *"Je veux faire de l'informatique, quelle filière choisir ?"* | Le bot ne recommande pas de filière immédiatement ; il demande le niveau (Bac/Licence), la section et la moyenne. | *À tester après intégration* | `À exécuter` |
| **QA-03** | **Orientation ciblée (Profil complet)** | *"J'ai un Bac Maths avec 14.5 et j'aime la programmation pratique."* | Comparaison claire entre Prépa intégrée et Licence Informatique à l'IIT + explication des passerelles vers le cycle ingénieur. | *À tester après intégration* | `À exécuter` |
| **QA-04** | **Suivi du contexte (Multi-tour)** | Tour 1 : *"Je suis en Bac Éco avec 13."* $\rightarrow$ Tour 2 : *"Quelles licences me conseillez-vous à l'ISB ?"* | Le bot retient le profil du Tour 1 (Bac Éco, 13) et recommande directement les licences de gestion/finance/marketing à l'ISB[cite: 11]. | *À tester après intégration* | `À exécuter` |
| **QA-05** | **Compréhension Tunisien & Arabizi** | *"Aslema, chkoun khir IIT wala ISB ken nheb el gestion ?"* | Comprend l'Arabizi/code-switching et oriente vers l'ISB (spécialisée en gestion/business) en distinguant l'IIT[cite: 11]. | *À tester après intégration* | `À exécuter` |
| **QA-06** | **Rattachement session invitée $\rightarrow$ compte** | Le visiteur discute en mode invité puis crée un compte / se connecte (`SA-29`). | L'historique de la conversation est conservé et rattaché au compte candidat sans perte de contexte[cite: 7]. | *À tester après intégration SA-29* | `À exécuter` |
| **QA-07** | **Hors-sujet & hors-périmètre** | *"Donne-moi la recette du couscous"* ou *"Valide mon admission tout de suite."* | Refus poli de répondre au hors-sujet ou de valider une admission officielle (réservée à un responsable humain), recentrage sur l'orientation[cite: 11]. | *À tester après intégration* | `À exécuter` |
| **QA-08** | **Gestion d'erreur technique (Timeout / LLM indisponible)** | Simuler une coupure ou un délai dépassé du fournisseur LLM (`SA-36`). | Message d'erreur clair et convivial affiché dans le chat sans plantage de l'interface ni perte des messages précédents. | *À tester après intégration SA-36* | `À exécuter` |

---

## 3. Registre des Anomalies Détectées

| ID Anomalie | Scénario lié | Description du problème | Gravité (`Mineure` / `Majeure` / `Bloquante`) | Responsable correction | Statut |
| :--- | :--- | :--- | :---: | :--- | :---: |
| *ANO-01* | *-* | *Aucune anomalie enregistrée (phase de préparation avant intégration).* | - | - | - |

---

## 4. Conclusion QA
* **Avancement :** Scénarios de recette préparés en amont (`Phase 5` du plan de travail)[cite: 11, 12].
* **Prochaine étape :** Exécution des tests croisés avec **Roua** (flux LLM/mémoire), **Manar** (sessions/compte) et **Tasnime** (dialecte) dès que le parcours conversationnel est connecté[cite: 11].

