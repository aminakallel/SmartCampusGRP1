// Un seul endroit à modifier si une route du projet est différente.
// `chat` pointe vers l'ancre "#chat" : c'est le widget flottant (monté dans le
// layout) qui s'ouvre. Le site est centré sur l'accueil (chat) et l'espace
// équipe (dashboard).
export const ROUTES = {
  home: "/",
  chat: "#chat",
  dashboard: "/dashboard",
} as const;
