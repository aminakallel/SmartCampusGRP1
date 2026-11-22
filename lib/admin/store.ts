import { useSyncExternalStore } from "react";
import { canAccess, ROLE_LABELS, type SessionUser } from "@/lib/admin/auth";
import { MOCK_PROGRAMMES } from "@/lib/mock-data";
import type { Programme } from "@/types";

/*
 * Base simulée dans le navigateur (localStorage), par appareil.
 * Pour brancher le vrai backend, remplacez les fonctions saveProgramme,
 * removeProgramme et restoreProgramme par des appels à lib/api-client.ts
 * (routes à valider avec l'équipe backend, SA-20).
 */

export type Statut = "publiee" | "brouillon";

export interface ProgrammeAdmin extends Programme {
  statut: Statut;
  updatedAt: string;
  updatedBy: string;
}

export type AuditAction = "création" | "modification" | "suppression" | "restauration" | "réinitialisation";

export interface AuditEntry {
  id: string;
  date: string;
  user: string;
  role: string;
  action: AuditAction;
  item: string;
  detail: string;
}

const KEY_PROGRAMMES = "smartcampus.mock.catalogue.v2";
const KEY_AUDIT = "smartcampus.mock.audit.v1";
const EMPTY_PROGRAMMES: ProgrammeAdmin[] = [];
const EMPTY_AUDIT: AuditEntry[] = [];

let programmes: ProgrammeAdmin[] | null = null;
let audit: AuditEntry[] | null = null;
const listeners = new Set<() => void>();

function seed(): ProgrammeAdmin[] {
  const now = new Date().toISOString();
  return MOCK_PROGRAMMES.map((p) => ({ ...p, statut: "publiee" as Statut, updatedAt: now, updatedBy: "Données initiales" }));
}

function read<T>(key: string, fallback: () => T): T {
  try {
    const raw = localStorage.getItem(key);
    if (raw) return JSON.parse(raw) as T;
  } catch {
    /* données illisibles : on repart des valeurs initiales */
  }
  return fallback();
}

function getProgrammes(): ProgrammeAdmin[] {
  if (programmes === null) programmes = read<ProgrammeAdmin[]>(KEY_PROGRAMMES, seed);
  return programmes;
}

function getAudit(): AuditEntry[] {
  if (audit === null) audit = read<AuditEntry[]>(KEY_AUDIT, () => []);
  return audit;
}

function persist() {
  try {
    localStorage.setItem(KEY_PROGRAMMES, JSON.stringify(programmes));
    localStorage.setItem(KEY_AUDIT, JSON.stringify(audit));
  } catch {
    /* stockage plein ou bloqué : les données restent en mémoire */
  }
  listeners.forEach((l) => l());
}

function log(user: SessionUser, action: AuditAction, item: string, detail: string) {
  const entry: AuditEntry = {
    id: crypto.randomUUID(),
    date: new Date().toISOString(),
    user: user.nom,
    role: ROLE_LABELS[user.role],
    action,
    item,
    detail,
  };
  audit = [entry, ...getAudit()].slice(0, 500);
}

function subscribe(callback: () => void) {
  listeners.add(callback);
  return () => {
    listeners.delete(callback);
  };
}

export function useAllProgrammes(): ProgrammeAdmin[] {
  return useSyncExternalStore(subscribe, getProgrammes, () => EMPTY_PROGRAMMES);
}

export function useAudit(): AuditEntry[] {
  return useSyncExternalStore(subscribe, getAudit, () => EMPTY_AUDIT);
}

/** false pendant le rendu serveur et l'hydratation, true ensuite. */
export function useHydrated(): boolean {
  return useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );
}

function assertAccess(user: SessionUser, p: Programme) {
  if (!canAccess(user, p.etablissement)) throw new Error("Accès refusé pour ce rôle.");
}

/** Crée ou modifie une formation (selon que l'id existe déjà). */
export function saveProgramme(input: ProgrammeAdmin, user: SessionUser) {
  assertAccess(user, input);
  const list = getProgrammes();
  const exists = list.some((p) => p.id === input.id);
  const next: ProgrammeAdmin = { ...input, updatedAt: new Date().toISOString(), updatedBy: user.nom };
  programmes = exists ? list.map((p) => (p.id === input.id ? next : p)) : [next, ...list];
  log(user, exists ? "modification" : "création", next.nom, `${next.etablissement}, ${next.niveau}, ${next.statut === "publiee" ? "publiée" : "brouillon"}`);
  persist();
}

/** Supprime une formation et la renvoie (pour pouvoir annuler). */
export function removeProgramme(id: string, user: SessionUser): ProgrammeAdmin | undefined {
  const target = getProgrammes().find((p) => p.id === id);
  if (!target) return undefined;
  assertAccess(user, target);
  programmes = getProgrammes().filter((p) => p.id !== id);
  log(user, "suppression", target.nom, target.etablissement);
  persist();
  return target;
}

export function restoreProgramme(p: ProgrammeAdmin, user: SessionUser) {
  assertAccess(user, p);
  programmes = [p, ...getProgrammes().filter((x) => x.id !== p.id)];
  log(user, "restauration", p.nom, "Suppression annulée");
  persist();
}

export function resetDemoData(user: SessionUser) {
  programmes = seed();
  audit = [];
  log(user, "réinitialisation", "Catalogue", "Données de démonstration rétablies");
  persist();
}