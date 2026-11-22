import { MOCK_PROGRAMMES } from "@/lib/mock-data";
import type { Programme } from "@/types";

/**
 * Intention détectée dans un message : oriente l'affichage côté chat.
 * - formations : des programmes correspondent à la question ;
 * - admission  : la question porte sur les conditions d'accès ;
 * - prospects  : la question porte sur les débouchés ;
 * - general    : question vague → toutes les formations ;
 * - none       : hors catalogue → aucune formation.
 */
export type ReplyIntent =
  | "formations"
  | "admission"
  | "prospects"
  | "general"
  | "none";

/** Réponse simulée du chat : une intention et les formations concernées. */
export interface AssistantReply {
  intent: ReplyIntent;
  programmes: Programme[];
}

/** Minuscules sans accents, pour comparer les mots-clés. */
function normalize(value: string): string {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

const ADMISSION_TERMS = [
  "condition",
  "admission",
  "prerequis",
  "requis",
  "dossier",
  "requirement",
  "eligibility",
];

const PROSPECT_TERMS = [
  "debouche",
  "debouch",
  "metier",
  "carriere",
  "emploi",
  "professionnel",
  "travail",
  "career",
  "job",
  "prospect",
  "salary",
];

/** Domaines absents du catalogue : la question reste sans réponse. */
const OFF_CATALOGUE_TERMS = [
  "droit",
  "medecine",
  "pharmacie",
  "commerce",
  "gestion",
  "lettres",
  "psychologie",
  "architecture",
  "journalisme",
  "marketing",
];

/** Termes comparables extraits d'une formation (normalisés). */
function searchTerms(programme: Programme): string[] {
  return [
    programme.nom,
    programme.etablissement,
    programme.niveau,
    programme.duree,
    ...programme.motsCles,
    ...programme.debouches,
    ...programme.prerequis,
  ].map(normalize);
}

/** La formation correspond-elle à la question ? (établissement, préfixes, sous-chaînes) */
function isMatch(programme: Programme, words: string[], text: string): boolean {
  if (programme.etablissement === "IIT" && text.includes("iit")) return true;
  if (programme.etablissement === "ISB" && text.includes("isb")) return true;

  return searchTerms(programme).some((term) =>
    words.some((word) => {
      if (word === term) return true;
      const [shorter, longer] =
        word.length <= term.length ? [word, term] : [term, word];
      return shorter.length >= 4 && longer.includes(shorter);
    }),
  );
}

/**
 * Réponse simulée, en attendant le branchement du LLM (tâches SA-36 / SA-37).
 *
 * Règles du mode mock :
 * - question sur les formations, un niveau, un établissement ou un domaine :
 *   renvoie les formations correspondantes du catalogue (lib/mock-data.ts) ;
 * - question sur les conditions d'admission ou les débouchés : renvoie les
 *   formations correspondantes en mettant ces champs en avant ;
 * - question vague ou sans mot-clé : renvoie toutes les formations ;
 * - question hors catalogue : ne renvoie aucune formation.
 *
 * Aucune information n'est inventée : tout provient de lib/mock-data.ts.
 */
export function buildMockReply(input: string): AssistantReply {
  const text = normalize(input);
  const words = text.split(/[^a-z0-9]+/).filter((word) => word.length >= 4);

  const wantsAdmission = ADMISSION_TERMS.some((term) => text.includes(term));
  const wantsProspects = PROSPECT_TERMS.some((term) => text.includes(term));
  const offCatalogue = OFF_CATALOGUE_TERMS.some((term) =>
    words.includes(term),
  );

  const matched = MOCK_PROGRAMMES.filter((programme) =>
    isMatch(programme, words, text),
  );

  if (matched.length === 0 && offCatalogue) {
    return { intent: "none", programmes: [] };
  }
  if (wantsAdmission) {
    return {
      intent: "admission",
      programmes: matched.length > 0 ? matched : MOCK_PROGRAMMES,
    };
  }
  if (wantsProspects) {
    return {
      intent: "prospects",
      programmes: matched.length > 0 ? matched : MOCK_PROGRAMMES,
    };
  }
  if (matched.length > 0) {
    return { intent: "formations", programmes: matched };
  }
  return { intent: "general", programmes: MOCK_PROGRAMMES };
}
