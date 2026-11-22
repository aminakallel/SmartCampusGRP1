/**
 * Configuration centrale du frontend.
 *
 * La connexion au backend FastAPI est pilotée par variables d'environnement :
 *   NEXT_PUBLIC_API_BASE_URL   : URL de base de l'API (ex. http://localhost:8000)
 *   NEXT_PUBLIC_USE_MOCK_API   : "true" pour forcer les données locales
 *   NEXT_PUBLIC_PREINSCRIPTION_URL : lien externe du formulaire de la faculté
 *
 * Tant que NEXT_PUBLIC_API_BASE_URL est vide, l'application fonctionne
 * uniquement avec des données mockées : aucun backend n'est requis.
 */

const rawBaseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "").trim();

const useMockOverride = process.env.NEXT_PUBLIC_USE_MOCK_API;

const rawPreinscriptionUrl = (
  process.env.NEXT_PUBLIC_PREINSCRIPTION_URL ?? ""
).trim();

export const apiConfig = {
  /** URL de base de l'API backend (chaîne vide si non configurée). */
  baseUrl: rawBaseUrl,
  /**
   * Mode mock : activé si l'URL n'est pas configurée, ou forcé explicitement
   * via NEXT_PUBLIC_USE_MOCK_API.
   */
  useMock: useMockOverride ? useMockOverride === "true" : rawBaseUrl.length === 0,
  /** L'API réelle est-elle configurée ? */
  isConfigured: rawBaseUrl.length > 0,
} as const;

export const appConfig = {
  name: "SmartCampus AI",
  tagline: "Plateforme agentique d'orientation universitaire",
  institution: "IIT & ISB",
  /**
   * URL du formulaire de préinscription de la faculté (lien externe).
   * Chaîne vide si non configurée : les boutons « Se préinscrire » sont masqués.
   */
  preinscriptionUrl: rawPreinscriptionUrl,
} as const;
