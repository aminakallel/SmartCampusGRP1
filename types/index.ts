/**
 * Types métier partagés du frontend SmartCampus AI.
 * Ces contrats servent de référence commune avec le backend FastAPI.
 */

/** Établissement proposant la formation. */
export type Etablissement = "IIT" | "ISB";

/** Niveau du parcours académique. */
export type NiveauFormation = "Licence" | "Préparatoire" | "Ingénierie" | "Master" | "Architecture";

/** Une formation du catalogue (IIT ou ISB). */
export interface Programme {
  id: string;
  slug: string;
  nom: string;
  etablissement: Etablissement;
  niveau: NiveauFormation;
  duree: string;
  description: string;
  prerequis: string[];
  debouches: string[];
  motsCles: string[];
  lien?: string;
}

/** Auteur d'un message de la conversation. */
export type MessageRole = "user" | "assistant" | "system";

/** Un message échangé dans la conversation. */
export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  /** Date ISO 8601 du message. */
  createdAt: string;
}

/** Une session de conversation (base de travail pour la mémoire, SA-26). */
export interface ChatSession {
  id: string;
  messages: ChatMessage[];
  createdAt: string;
  updatedAt: string;
}
