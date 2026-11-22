# Audit technique — nouveau livrable SA-14 d’Amina

**Date de l’audit : 22 novembre 2026**  
**Objet audité :** `C:\Users\dhieb\Downloads\SA-14_Conception_Tables_Gestion (1).md`, incluant le script SQL intégré en section 4.  
**Périmètre :** revue statique seulement. Le SQL n’a pas été exécuté et aucune migration métier n’a été lancée.

## Résumé

Le nouveau modèle aligne les FK sur `utilisateur(id UUID)` et `formations_parcours(id INTEGER)`. Les références `NEW.utilisateur_id`, `NEW.decision_par_admin_id` et `NEW.admin_id` correspondent aux colonnes déclarées et ciblées par les triggers. La fonction `mettre_a_jour_modifie_le()` est présente dans le DDL SA-13 fourni et affecte `NEW.modifie_le`.

**Décision d’intégration : WARNING — ne pas exécuter tel quel avant corrections.** Les principaux points à corriger sont la cohérence des états de rendez-vous, les invariants QCM et la répétabilité du script. La syntaxe paraît cohérente à la lecture, mais aucun parseur PostgreSQL ni serveur de test n’a validé le SQL. Le dépôt ne contient pas de fichier `migration_SA14_gestion.sql` autonome.

## Résultats détaillés

| Statut | Fichier / emplacement | Constat, risque et proposition |
|---|---|---|
| PASS | Nouveau SA-14, §3.1 et §4, `utilisateur_id`, `decision_par_admin_id`; `verifier_roles_dossier()` | Les colonnes `NEW.utilisateur_id` et `NEW.decision_par_admin_id` existent sur `dossier_candidature`. Les deux sont des UUID vers `utilisateur(id UUID)`. Le trigger les lit correctement. Si le SELECT ne trouve rien, la variable reste NULL et `IS DISTINCT FROM` rejette la ligne; la FK rejette aussi l’identifiant inexistant. |
| PASS | Nouveau SA-14, §3.5 et §4, `rendez_vous.admin_id`; `verifier_admin_rdv()` | `NEW.admin_id` existe et référence `utilisateur(id)` en UUID. Le trigger vérifie le rôle `admin` lorsqu’il est non NULL; le NULL est permis selon la FK nullable. |
| PASS | Nouveau SA-14, §4, FKs SA-13/SA-12 | `utilisateur_id`, `decision_par_admin_id` et `admin_id` sont UUID vers `utilisateur(id)`. `parcours_id` et `parcours_cible_id` sont INTEGER vers `formations_parcours(id)`. Types alignés sur les décisions confirmées et conceptions fournies. |
| PASS | PDF SA-13 de Manar, page 7; nouveau SA-14, §4 | `mettre_a_jour_modifie_le()` est effectivement défini dans le DDL SA-13 : il affecte `NEW.modifie_le = now()` et retourne NEW. Les trois tables qui l’appellent ont cette colonne. L’ordre d’application doit rester après SA-13. |
| PASS | Nouveau SA-14, §4, types enum | Les quatre types `statut_dossier`, `statut_qcm`, `modalite_rdv`, `statut_rdv` sont créés avant usage. Valeurs par défaut compatibles avec leurs types respectifs. |
| PASS | Nouveau SA-14, §4, contraintes numériques/temporelles | `ck_qcm_index` interdit un index négatif; `ck_qcm_total` exige plus de zéro question; `ck_qcm_score` accepte NULL ou 0–100; `ck_question_ordre` exige ordre ≥1; `ck_rdv_horaires` exige fin > début. Syntaxe plausible pour PostgreSQL 16. |
| PASS | Nouveau SA-14, §4, index et unicité | `utilisateur_id UNIQUE` autorise un dossier au plus par utilisateur; `source_webhook_id UNIQUE` assure l’idempotence des valeurs non NULL; `(tentative_id, ordre) UNIQUE` interdit les ordres dupliqués dans une tentative. Les index explicites couvrent statut/parcours dossier, compléments, tentatives et dossier/statut rendez-vous. L’index composite questions sert aussi les recherches par `tentative_id`. |
| PASS | Nouveau SA-14, §4, `ON DELETE` | Suppression du candidat cascade vers dossier; suppressions du dossier/tentative cascade vers enfants; suppression d’un parcours est RESTRICT; suppression de l’admin décisionnaire ou affecté met la référence à NULL. Ces effets sont syntaxiquement cohérents; la cascade candidat reste une décision de conservation des données à confirmer. |
| WARNING | Nouveau SA-14, §4, `ck_rdv_validation_admin` (lignes 314–317) | Le CHECK autorise `valide_par_admin=TRUE` avec n’importe quel statut (`propose`, `indisponible` compris), et `statut='confirme'` avec `admin_id IS NULL`. Le trigger ne requiert pas d’admin pour un rendez-vous confirmé. Définir les transitions; confirmer si confirmation implique admin non NULL et `valide_par_admin=TRUE`; préciser le sens de `indisponible`. |
| WARNING | Nouveau SA-14, §3.5/§4, `rendez_vous` | `valide_par_admin` et `admin_id` peuvent diverger dans les deux sens. La modalité ne contraint pas `lien_ou_salle`. Ajouter une contrainte cohérente ou représenter explicitement les états, et valider le besoin d’un lien/salle selon la modalité. |
| WARNING | Nouveau SA-14, §3.3–3.4/§4, QCM | Le DDL ne borne pas `derniere_question_idx` par `nb_total_questions`, ne lie pas `termine_le` au statut `termine`, et ne garantit pas le nombre réel de questions égal à `nb_total_questions`. Le diagramme promet au moins une question, mais le DDL n’impose aucune ligne enfant. Définir ces invariants au service dans une transaction ou par mécanisme différé; interdire les modifications après clôture si requis. |
| WARNING | Nouveau SA-14, §3.1/§4, dossier | `utilisateur_id UNIQUE` impose un dossier maximum par utilisateur, même pour des parcours successifs. Confirmer cette règle. Un dossier `accepte`/`refuse` n’est pas contraint à avoir `decision_par_admin_id`; ajouter une règle de transition exigeant le décideur si c’est obligatoire. |
| WARNING | Nouveau SA-14, §4, DDL | `CREATE TYPE`, tables, indexes et triggers ne sont pas idempotents. Une seconde exécution échoue sur les objets existants; une interruption peut laisser un schéma partiel selon le client. Placer le SQL dans une migration versionnée, transactionnelle si possible, avec stratégie d’évolution/rollback. Ne pas ajouter simplement `IF NOT EXISTS` sans vérifier la définition existante. |
| WARNING | Nouveau SA-14, triggers de rôle et SA-13 | Un changement ultérieur du rôle dans `utilisateur` peut invalider des références existantes. Le contrôle par SELECT ne verrouille pas l’utilisateur; un changement concurrent de rôle peut survenir après contrôle. Définir une politique de changement de rôle avec références, et verrouillage/validation transactionnelle adaptés. |
| WARNING | Nouveau SA-14, §4, index (lignes 379–398) | Pas d’index explicite sur `rendez_vous.admin_id` ni `dossier_candidature.decision_par_admin_id`. PostgreSQL ne crée pas d’index côté FK automatiquement; suppression/changement de PK parent et requêtes par admin peuvent scanner les tables. Ajouter selon les accès attendus. |
| WARNING | Nouveau SA-14, UUID/migrations | `gen_random_uuid()` est disponible dans PostgreSQL 16. La migration actuelle `backend/migrations/0000_enable_extensions.sql` active `pgcrypto` et `vector`, mais ne crée aucune table SA-14. `vector` n’est pas utilisé par ce schéma de gestion. |
| WARNING | Nouveau SA-14, `donnees_admin_json` et données de QCM/RDV | Le JSON administratif peut contenir CIN et pièces (décrit §3.1), mais le schéma ne spécifie pas de politique de moindre privilège, rétention, chiffrement applicatif ou audit d’accès. PostgreSQL stocke ces valeurs en clair au niveau logique; une fuite de logs/export peut exposer des données personnelles. Définir les rôles SQL, les permissions API, la rétention et le traitement des pièces avant production; ne jamais journaliser ces colonnes. |
| BLOCKED | Validation syntaxique PostgreSQL 16 | SQL non exécuté; aucun parseur PostgreSQL n’est disponible dans l’environnement vérifié. La lecture statique ne prouve pas que PostgreSQL 16 accepte tout le script. Après corrections, valider sur une base jetable PG16 avec SA-12/SA-13 installés, jamais sur Odoo ou la base locale persistante. |
| BLOCKED | Présence réelle des schémas référencés | Le checkout ne contient pas les migrations métier SA-12/SA-13 ni leurs tables. Les documents donnent le contrat de référence, mais l’application des FK/triggers dans le bon ordre n’a pas pu être testée. La fonction d’audit est visible dans le DDL PDF SA-13; sa présence dans une base cible n’est pas démontrée. |
| BLOCKED | Intégration migration/livrable | Le SQL est fourni dans le Markdown, mais le dépôt ne contient ni fichier `migration_SA14_gestion.sql` autonome ni système de migration versionnée; seule `0000_enable_extensions.sql` est présente. Il manque donc un livrable d’intégration traçable. Ce constat ne signifie pas que la syntaxe SQL est invalide. Aucun SQL n’a été exécuté. |

## Nommage et mapping

Le nouveau SA-14 emploie `parcours_id` pour le parcours du dossier et `parcours_cible_id` pour celui du QCM. La conception SA-12 nomme la table `formations_parcours`; ses tables de critères et de documents emploient aussi `parcours_id`. **Convention recommandée : retenir les noms du nouveau SA-14**, qui reflètent le domaine « parcours », avec les deux FK INTEGER. Conserver ces noms sans introduire d’alias concurrents.

Le nouveau livrable utilise des tables singulières : `dossier_candidature`, `dossier_complement`, `qcm_tentative`, `qcm_question`, `rendez_vous`. Le document précédent utilisait des noms différents. Traiter le nouveau livrable comme la version courante et éviter de combiner les deux listes dans une migration.

## Inventaire et protections

- Présents : le nouveau Markdown SA-14 en pièce jointe; `backend/migrations/0000_enable_extensions.sql`; la proposition de mapping.
- Absents du checkout : fichier SQL SA-14 autonome et migrations métier SA-12/SA-13.
- Aucun SQL exécuté; aucune migration métier créée ou modifiée; aucune donnée changée; PostgreSQL Odoo port 5432 non touché.
- Aucun commit ni push.

## Prochaines étapes recommandées

1. Faire préciser/corriger les règles d’état rendez-vous et rendre `admin_id`, `valide_par_admin`, `statut` cohérents.
2. Confirmer un dossier maximum par utilisateur, la cascade à la suppression et l’obligation de l’administrateur pour les décisions finales.
3. Fixer les invariants QCM : progression, compte des questions, statut/horodatage, minimum de questions et immutabilité après clôture.
4. Ajouter les index Admin utiles et définir la politique de changement de rôle, y compris les transactions concurrentes.
5. Obtenir les migrations versionnées SA-12/SA-13; extraire SA-14 dans une migration versionnée et transactionnelle après validation.
6. Valider le SQL sur une base PostgreSQL 16 jetable, puis créer des tests d’intégration et des scénarios de concurrence. Ne pas employer la base locale persistante ni PostgreSQL Odoo.


