# Design system SmartCampus AI

## Objectif
Interface moderne, sobre et institutionnelle pour des candidats (lycéens, parents). Elle doit inspirer confiance en 5 secondes. Une seule chose spectaculaire par page ; tout le reste reste calme.

## Couleurs (tokens dans app/globals.css, via @theme et variables CSS)
Clair : ink #0F2447, iit #1F5FBF, isb #15784A, surface #FFFFFF, paper #F6F8FB, line #D9E0EA, muted #51607A.
Sombre (prefers-color-scheme: dark) : fond #0B1220, surface #111A2E, line #22304A, texte #E6ECF7, muted #93A1BC, iit #5B9BFF, isb #3DBE8B.
Règle : bleu = IIT, vert = ISB, partout (badges, bordures). Aucune autre couleur d’accent.

## Typographie
IBM Plex Sans + IBM Plex Sans Arabic (next/font/google, variables --font-plex et --font-plex-ar).
h1 36 à 48 px semibold, h2 28 px, h3 18 px, texte 16 px, secondaire 14 px. Lignes de 70 caractères maximum. Texte arabe : dir="auto".

## Mise en page
Conteneur max-w-6xl, px-5. Sections py-16 (hero py-24). Alterner fond blanc et fond paper. Texte aligné à gauche, sauf le bandeau final.

## Composants
Rayons : boutons et champs 8 px, cartes 12 px, badges en pilule. Bordures 1 px. Ombres seulement au survol des éléments cliquables. Pas de dégradés décoratifs, pas d’emoji.
Button : primary (iit), secondary (bordure), ghost ; 44 px de hauteur minimum ; états disabled et loading.
Badge : tons iit, isb, neutre, succès, attention.
Champs : label visible, texte d’aide, erreur écrite (pas seulement colorée).
États obligatoires : chargement (skeleton), vide (dit quoi faire), erreur (dit ce qui s’est passé et comment corriger).

## Mouvement
Aucune animation d’entrée. Transitions de 150 ms sur hover et focus. Respecter prefers-reduced-motion.

## Accessibilité
Contraste AA, :focus-visible 2 px iit, landmarks (header, nav, main, footer), lien « Aller au contenu », aria-live="polite" sur les messages du chat.

## Rédaction
Vouvoiement, phrases courtes, casse de phrase. Boutons avec un verbe : « Parler à l’assistant », « Se préinscrire ». Aucun jargon côté candidat (RAG, LangGraph, LLM, human-in-the-loop). Ne rien promettre qui n’existe pas : fonctionnalité non livrée = badge « Bientôt » ; données fictives = mention « Exemple » ou « Données de démonstration ». Apostrophe typographique ’.

## Interdits
Étiquettes en MAJUSCULES au-dessus des titres, chiffres de remplissage (24/7, « 5 étapes »), un seul mot coloré dans un titre, cartes identiques partout, « → » ajouté aux boutons.

## Périmètre (mis à jour)
Le site est centré sur le chat. Pages conservées : accueil (chat) et dashboard (espace équipe). Pages supprimées : préinscription, catalogue/formations, comment ça marche. La préinscription se fait sur le site de la faculté (lien externe via NEXT_PUBLIC_PREINSCRIPTION_URL). Le chat répond avec les formations issues de lib/mock-data.ts.

## Mouvement : exception pour le chat
Seule animation d’entrée autorisée : l’ouverture automatique du chat à l’arrivée sur le site (250 à 350 ms, translation + fondu). Désactivée avec prefers-reduced-motion.
