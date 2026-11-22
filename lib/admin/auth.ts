import { useSyncExternalStore } from "react";
import type { Etablissement } from "@/types";

/*
 * ATTENTION : connexion de DÉMONSTRATION, ce n'est PAS de la sécurité.
 * Les comptes sont écrits en clair dans le code et la session est dans le
 * navigateur. L'authentification réelle (JWT, rôles) viendra du backend.
 */

export type Role = "admin" | "resp-iit" | "resp-isb";

export interface SessionUser {
  email: string;
  nom: string;
  role: Role;
  /** null = accès à tous les établissements. */
  etablissement: Etablissement | null;
}

export const ROLE_LABELS: Record<Role, string> = {
  admin: "Administrateur",
  "resp-iit": "Responsable IIT",
  "resp-isb": "Responsable ISB",
};

export const DEMO_ACCOUNTS: Array<SessionUser & { password: string }> = [
  { email: "admin@smartcampus.test", password: "demo1234", nom: "Administrateur", role: "admin", etablissement: null },
  { email: "resp.iit@smartcampus.test", password: "demo1234", nom: "Responsable IIT", role: "resp-iit", etablissement: "IIT" },
  { email: "resp.isb@smartcampus.test", password: "demo1234", nom: "Responsable ISB", role: "resp-isb", etablissement: "ISB" },
];

const KEY = "smartcampus.mock.session.v1";
const listeners = new Set<() => void>();
let cachedRaw: string | null | undefined;
let cachedUser: SessionUser | null = null;

function getSnapshot(): SessionUser | null {
  const raw = sessionStorage.getItem(KEY);
  if (raw !== cachedRaw) {
    cachedRaw = raw;
    try {
      cachedUser = raw ? (JSON.parse(raw) as SessionUser) : null;
    } catch {
      cachedUser = null;
    }
  }
  return cachedUser;
}

function subscribe(callback: () => void) {
  listeners.add(callback);
  return () => {
    listeners.delete(callback);
  };
}

/** undefined = pas encore connu (rendu serveur) ; null = aucune session. */
export function useSession(): SessionUser | null | undefined {
  return useSyncExternalStore<SessionUser | null | undefined>(subscribe, getSnapshot, () => undefined);
}

export function login(email: string, password: string): SessionUser | null {
  const account = DEMO_ACCOUNTS.find(
    (a) => a.email === email.trim().toLowerCase() && a.password === password,
  );
  if (!account) return null;
  const user: SessionUser = {
    email: account.email,
    nom: account.nom,
    role: account.role,
    etablissement: account.etablissement,
  };
  sessionStorage.setItem(KEY, JSON.stringify(user));
  listeners.forEach((l) => l());
  return user;
}

export function logout() {
  sessionStorage.removeItem(KEY);
  listeners.forEach((l) => l());
}

export function canAccess(user: SessionUser, etablissement: Etablissement): boolean {
  return user.etablissement === null || user.etablissement === etablissement;
}