"use client";

import {
  createContext,
  useContext,
  useMemo,
  type ReactNode,
} from "react";
import { fr } from "./fr";
import type { Translation } from "./types";

type LanguageContextValue = {
  dict: Translation;
};

const LanguageContext = createContext<LanguageContextValue | null>(null);

/**
 * Provider i18n — le site est uniquement en français (voir DESIGN.md).
 * Le type Language et la logique de bascule ont été retirés.
 */
export function LanguageProvider({ children }: { children: ReactNode }) {
  const value = useMemo<LanguageContextValue>(() => ({ dict: fr }), []);

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

/**
 * Résout une clé à points (ex: "nav.formations") dans l'objet de traduction.
 * Retourne la chaîne trouvée, ou la clé elle-même si la résolution échoue.
 */
function resolvePath(source: unknown, path: string): unknown {
  return path
    .split(".")
    .reduce<unknown>(
      (acc, part) =>
        acc && typeof acc === "object" && part in (acc as Record<string, unknown>)
          ? (acc as Record<string, unknown>)[part]
          : undefined,
      source,
    );
}

export function useTranslation() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useTranslation must be used within a LanguageProvider");
  }

  const { dict } = context;

  const t = (key: string): string => {
    const value = resolvePath(dict, key);
    return typeof value === "string" ? value : key;
  };

  return { t, dict };
}
