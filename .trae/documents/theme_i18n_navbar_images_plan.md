# Thème sombre, i18n FR/EN, navbar moderne et images — Plan d’implémentation

## Recherche repository

### Stack
- **Next.js 16.4.6** avec `cacheComponents: true` et `partialPrefetching: true` (voir `next.config.ts`).
- **Tailwind CSS v4** (`@import "tailwindcss"` + `@theme inline` dans `app/globals.css`).
- TypeScript strict, alias `@/*`.

### Contraintes clés liées à cacheComponents
- Le layout racine (`app/layout.tsx`) est un composant serveur. Il **ne doit pas** lire `cookies()`/`headers()` sans `<Suspense>` (risque de casser le shell statique).
- Solution retenue pour le thème et la langue : **provider React côté client + `localStorage`**, avec un script inline dans `<head>` pour le thème (anti-flash).

### État actuel
- Thème : uniquement `prefers-color-scheme` dans `app/globals.css` (pas d’attribut `data-theme`).
- Pas d’i18n : tous les textes sont codés en dur en français.
- Header actuel (`components/site/Header.tsx`) : simple, liens en dur, pas de thème/langue, menu `<details>` basique.
- Footer (`components/site/Footer.tsx`) : textes en dur en français.
- Page d’accueil (`app/page.tsx`) : tout en français, pas d’images.
- Chat : `lib/assistant.ts` contient `WELCOME_MESSAGE`, `CHAT_SUGGESTIONS`, `buildMockReply`. `buildMockReply` est la logique (à conserver) ; les deux constantes sont des données textuelles.
- Polices : `IBM_Plex_Sans` + `IBM_Plex_Sans_Arabic` via `next/font/google`, variables `--font-plex` et `--font-plex-ar`.

### Guides Next.js lus
- `cacheComponents.md` : PPR par défaut, shell statique, navigation avec `<Activity>`.
- `13-fonts.md` : `next/font/google` self-hosté, `variable` pour les CSS vars.
- `script.md` : `strategy="beforeInteractive"` pour les scripts avant hydratation (doit être dans le root layout).
- `image.md` : `next/image` avec `width`/`height` ou `fill`, `priority`, `sizes`, `quality`.

## Fichiers et modules

### Nouveaux fichiers
- `lib/i18n/fr.ts` — traductions françaises (clés organisées par page).
- `lib/i18n/en.ts` — traductions anglaises (mêmes clés).
- `lib/i18n/index.ts` — types `Translation`, `Language`, `LanguageProvider`, hook `useTranslation`.
- `components/providers/theme-provider.tsx` — `ThemeProvider` client (localStorage + `data-theme`).
- `components/providers/index.tsx` — wrapper `Providers` (ThemeProvider + LanguageProvider).
- `public/images/hero.svg`, `public/images/iit.svg`, `public/images/isb.svg` — illustrations SVG de remplacement.

### Fichiers modifiés
- `app/globals.css` — `data-theme` au lieu de `prefers-color-scheme` uniquement, `@custom-variant dark`, conservation du fallback `prefers-color-scheme`.
- `app/layout.tsx` — `suppressHydrationWarning` sur `<html>`, script anti-flash, providers, `lang` dynamique.
- `components/site/Header.tsx` — refonte complète (logo, liens centrés + état actif, sélecteur FR|EN, bouton thème, bouton CTA, menu mobile).
- `components/site/Footer.tsx` — traduction des textes.
- `app/page.tsx` — traduction + ajout des images (hero + cartes IIT/ISB).
- `components/chat/chat-conversation.tsx` — traduction UI (suggestions, placeholder, erreur, aria-labels).
- `components/chat/chat-widget.tsx` — traduction UI (placeholder, aria-labels).
- `lib/assistant.ts` — déplacement de `WELCOME_MESSAGE` et `CHAT_SUGGESTIONS` vers i18n (la logique `buildMockReply` reste intacte).

### Non modifiés (hors périmètre)
- `lib/services/*`, `types/*`, `lib/mock-data.ts`, `next.config.ts`.
- Logique d’envoi du chat (`buildMockReply`, gestion des messages).

## Étapes d’implémentation (ordre de dépendance)

### 1. Tokens de thème (`app/globals.css`)
- Remplacer `@media (prefers-color-scheme: dark)` par un bloc `[data-theme="dark"]` pour les tokens sombres.
- **Conserver** un bloc `@media (prefers-color-scheme: dark)` en fallback (pour les visiteurs sans choix mémorisé et sans JS).
- Ajouter `@custom-variant dark (&:where([data-theme="dark"], [data-theme="dark"] *));` après `@import "tailwindcss"`.

### 2. Script anti-flash et layout (`app/layout.tsx`)
- Ajouter `suppressHydrationWarning` sur `<html>`.
- Ajouter `<Script id="theme-init" strategy="beforeInteractive">` qui lit `localStorage.getItem("theme")` et applique `data-theme` (fallback sur `prefers-color-scheme`).
- Importer le composant `Providers` et l’englobe autour de `<Header />`, `<main>`, `<Footer />`, `<ChatWidget />`.

### 3. ThemeProvider (`components/providers/theme-provider.tsx`)
- `"use client"`.
- État `theme: "light" | "dark"`, initialisé depuis `localStorage` (sinon `prefers-color-scheme`).
- `useEffect` synchronise `document.documentElement.dataset.theme` et écrit dans `localStorage`.
- Expose `theme`, `toggleTheme`, `setTheme`.

### 4. i18n (`lib/i18n/`)
- `fr.ts` et `en.ts` : objet `Translation` typé, clés organisées par page (`nav`, `footer`, `home`, `chat`, `common`).
- `index.ts` : `type Language = "fr" | "en"`, `LanguageProvider` (client, localStorage, met à jour `document.documentElement.lang`), `useTranslation()` retourne `{ t, language, setLanguage }`.
- `t(key)` utilise une notation par points (`t("nav.formations")`).

### 5. Providers wrapper (`components/providers/index.tsx`)
- `"use client"`, englobe `ThemeProvider` + `LanguageProvider`.

### 6. Navbar (`components/site/Header.tsx`)
- `"use client"` (utilise `usePathname`, `useTranslation`, `useTheme`).
- Desktop : logo à gauche, liens centrés (soulignement 2 px `iit` sur l’actif via `usePathname`), à droite : sélecteur FR|EN (segmenté, `aria-label`), bouton thème (soleil/lune, `aria-label`, `aria-pressed`), bouton « Parler à l’assistant ».
- Sticky, `bg-surface/95 backdrop-blur`, `border-b border-line`.
- Mobile (`< 768 px`) : bouton menu avec `aria-expanded`, panneau plein largeur (liens, langue, thème, CTA), fermeture par Échap, focus trap léger.
- Cibles tactiles ≥ 44 px, `:focus-visible`, transitions 150 ms, aucune animation d’entrée.
- « Admissions » reste dans le footer uniquement.

### 7. Footer (`components/site/Footer.tsx`)
- Convertir en client (ou utiliser un composant client enfant) pour `useTranslation`.
- Traduire tous les textes.

### 8. Page d’accueil (`app/page.tsx`)
- Traduire tous les textes via `useTranslation` (composant client ou sous-composant client).
- **Hero** : ajouter `next/image` dans la colonne de droite (sous ou à côté de la démo), `priority`, `sizes="(max-width: 768px) 100vw, 50vw"`, coins 12 px.
- **Cartes IIT/ISB** : image en haut, conteneur `aspect-[3/2]`, `next/image fill object-cover`, liseré `border-t-4 border-iit` / `border-isb`.
- `alt` traduits (fr/en) via i18n.

### 9. Chat (`chat-conversation.tsx`, `chat-widget.tsx`)
- Utiliser `useTranslation` pour les textes UI.
- `WELCOME_MESSAGE` et `CHAT_SUGGESTIONS` : récupérés depuis i18n (`t("chat.welcome")`, `t("chat.suggestions")`) au lieu de `lib/assistant.ts`.
- `buildMockReply` reste importé de `lib/assistant.ts` (logique intacte).
- Traduire : placeholder, message d’erreur, bouton « Réessayer », aria-labels, « En ligne », « Mode démonstration », « Entrée pour envoyer… ».

### 10. Nettoyage `lib/assistant.ts`
- Retirer `WELCOME_MESSAGE` et `CHAT_SUGGESTIONS` (déplacés dans i18n).
- Conserver `buildMockReply`.

### 11. SVG de remplacement (`public/images/*.svg`)
- `hero.svg` (1600×1000), `iit.svg` (1200×800), `isb.svg` (1200×800).
- Illustration abstraite sobre, couleurs `iit` (#1F5FBF) et `isb` (#15784A), sans texte, sans personnage, sans dégradé criard.

### 12. Validation
- `npm run lint`
- `npm run build`
- Vérifier le rendu en 375/768/1280 px, clair/sombre, FR/EN.

## Dépendances et considérations

- **cacheComponents** : aucun accès à `cookies()`/`headers()` dans le layout. Le thème et la langue sont 100 % côté client.
- **Hydratation** : `suppressHydrationWarning` sur `<html>` pour `data-theme` et `lang` (le script anti-flash modifie le DOM avant React).
- **Tailwind v4** : `@custom-variant dark` doit être déclaré après `@import "tailwindcss"`.
- **Polices** : IBM Plex Sans + Arabic déjà en place, aucune modification.
- **`lib/assistant.ts`** : seules les constantes textuelles sont déplacées ; `buildMockReply` (logique) reste intact.
- **`next/image`** : les SVG sont optimisés par Next.js. `width`/`height` fournis ou `fill` avec conteneur `aspect-ratio`.
- **i18n** : pas de bibliothèque ajoutée. Les clés sont typées (TypeScript garantit l’égalité fr/en).

## Validation

- `npm run lint` sans erreur ni avertissement.
- `npm run build` réussi (toutes les pages générées).
- Vérification manuelle :
  - Thème clair/sombre bascule sans flash, persiste après reload.
  - Langue FR/EN bascule, `<html lang>` mis à jour, persiste.
  - Navbar responsive : desktop centré, mobile avec menu, Échap ferme.
  - Images hero + cartes IIT/ISB s’affichent, `alt` présents.
  - Chat : suggestions/placeholder/erreurs traduits.

## Risques

- **Hydratation mismatch** : atténué par `suppressHydrationWarning` et le script anti-flash avant React.
- **Types i18n** : si `fr.ts` et `en.ts` divergent, TypeScript échoue → vérifié au build.
- **SVG trop lourds** : garder les SVG simples (< 10 Ko) pour respecter la limite de 300 Ko.
- **Menu mobile** : bien fermer le panneau lors de la navigation (changement de `pathname`).
