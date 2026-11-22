export interface NavItem {
  label: string;
  href: string;
  description: string;
}

/**
 * Navigation principale de l'application.
 * Le site est centré sur le chat : seuls l'accueil et l'espace équipe subsistent.
 * La préinscription est un lien externe (NEXT_PUBLIC_PREINSCRIPTION_URL) et non
 * une route interne.
 */
export const NAV_ITEMS: NavItem[] = [
  {
    label: "Accueil",
    href: "/",
    description: "Assistant d’orientation",
  },
];
