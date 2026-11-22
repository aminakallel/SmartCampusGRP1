"use client";

import { useEffect, useMemo, useState } from "react";
import { AdminIcon } from "@/components/admin/admin-icon";
import ProgrammeForm from "@/components/admin/programme-form";
import Button from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { canAccess, useSession } from "@/lib/admin/auth";
import {
  removeProgramme,
  restoreProgramme,
  saveProgramme,
  useAllProgrammes,
  useHydrated,
  type ProgrammeAdmin,
  type Statut,
} from "@/lib/admin/store";
import { cn } from "@/lib/cn";
import type { Etablissement } from "@/types";

const dateFormat = new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium", timeStyle: "short" });
const filterControl = "h-11 rounded-lg border border-line bg-surface px-3 text-sm text-ink";
const iconButton = "inline-flex h-11 w-11 items-center justify-center rounded-lg text-muted transition-colors duration-150 hover:bg-surface-muted hover:text-ink";

type Toast = { message: string; undo?: () => void };

function StatusLabel({ statut }: { statut: Statut }) {
  return statut === "publiee" ? (
    <span className="inline-flex items-center gap-1.5 text-sm text-success">
      <AdminIcon name="check" size={16} />
      Publiée
    </span>
  ) : (
    <span className="inline-flex items-center gap-1.5 text-sm text-muted">
      <AdminIcon name="draft" size={16} />
      Brouillon
    </span>
  );
}

function SchoolBadge({ etablissement }: { etablissement: Etablissement }) {
  return (
    <span className={cn("inline-flex rounded-full border px-2.5 py-0.5 text-xs font-semibold", etablissement === "IIT" ? "border-iit text-iit" : "border-isb text-isb")}>
      {etablissement}
    </span>
  );
}

export default function FormationsPage() {
  const user = useSession();
  const all = useAllProgrammes();
  const hydrated = useHydrated();
  const [query, setQuery] = useState("");
  const [etab, setEtab] = useState<"" | Etablissement>("");
  const [statut, setStatut] = useState<"" | Statut>("");
  /** undefined = fermé ; null = nouvelle formation. */
  const [editing, setEditing] = useState<ProgrammeAdmin | null | undefined>(undefined);
  const [toDelete, setToDelete] = useState<ProgrammeAdmin | null>(null);
  const [toast, setToast] = useState<Toast | null>(null);

  useEffect(() => {
    if (!toast) return;
    const id = window.setTimeout(() => setToast(null), 6000);
    return () => window.clearTimeout(id);
  }, [toast]);

  useEffect(() => {
    if (!toDelete) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setToDelete(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [toDelete]);

  const visible = useMemo(() => (user ? all.filter((p) => canAccess(user, p.etablissement)) : []), [all, user]);
  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    return visible.filter(
      (p) =>
        (!etab || p.etablissement === etab) &&
        (!statut || p.statut === statut) &&
        (!q || `${p.nom} ${p.niveau} ${p.motsCles.join(" ")}`.toLowerCase().includes(q)),
    );
  }, [visible, query, etab, statut]);

  if (!user) return null;

  const stats = [
    { label: "Formations", value: visible.length },
    { label: "IIT", value: visible.filter((p) => p.etablissement === "IIT").length },
    { label: "ISB", value: visible.filter((p) => p.etablissement === "ISB").length },
    { label: "Brouillons", value: visible.filter((p) => p.statut === "brouillon").length },
  ];
  const incomplete = visible.filter((p) => p.prerequis.length === 0 || p.debouches.length === 0).length;

  function handleSave(programme: ProgrammeAdmin) {
    if (!user) return;
    try {
      saveProgramme(programme, user);
      setToast({ message: "Formation enregistrée." });
      setEditing(undefined);
    } catch {
      setToast({ message: "Action refusée pour votre rôle." });
    }
  }

  function confirmDelete() {
    if (!user || !toDelete) return;
    const removed = removeProgramme(toDelete.id, user);
    setToDelete(null);
    if (removed) {
      setToast({ message: `« ${removed.nom} » supprimée.`, undo: () => restoreProgramme(removed, user) });
    }
  }

  return (
    <Container className="flex flex-col gap-6 py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-ink">Formations</h1>
          <p className="mt-1 text-sm text-muted">
            Le catalogue lu par l’assistant. {user.etablissement ? `Vous gérez l’${user.etablissement}.` : "Vous gérez l’IIT et l’ISB."}
          </p>
        </div>
        <Button onClick={() => setEditing(null)}>
          <AdminIcon name="plus" />
          Ajouter une formation
        </Button>
      </header>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {stats.map((s) => (
          <div key={s.label} className="rounded-xl border border-line bg-surface p-4">
            <p className="text-sm text-muted">{s.label}</p>
            <p className="mt-1 text-2xl font-semibold text-ink">{hydrated ? s.value : "–"}</p>
          </div>
        ))}
      </div>

      {incomplete > 0 ? (
        <p className="border-l-4 border-warning bg-surface px-4 py-3 text-sm text-ink">
          {incomplete} formation{incomplete > 1 ? "s" : ""} sans conditions d’accès ou sans débouchés : complétez-{incomplete > 1 ? "les" : "la"} pour que l’assistant réponde avec précision.
        </p>
      ) : null}

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative min-w-56 flex-1">
          <span className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-muted">
            <AdminIcon name="search" size={16} />
          </span>
          <input type="search" aria-label="Rechercher une formation" placeholder="Rechercher une formation" value={query} onChange={(e) => setQuery(e.target.value)} className={cn(filterControl, "w-full pl-9")} />
        </div>
        {user.etablissement === null ? (
          <select aria-label="Filtrer par établissement" value={etab} onChange={(e) => setEtab(e.target.value as "" | Etablissement)} className={filterControl}>
            <option value="">Tous les établissements</option>
            <option value="IIT">IIT</option>
            <option value="ISB">ISB</option>
          </select>
        ) : null}
        <select aria-label="Filtrer par statut" value={statut} onChange={(e) => setStatut(e.target.value as "" | Statut)} className={filterControl}>
          <option value="">Tous les statuts</option>
          <option value="publiee">Publiée</option>
          <option value="brouillon">Brouillon</option>
        </select>
      </div>

      {!hydrated ? (
        <div className="h-64 animate-pulse rounded-xl bg-surface-muted" aria-busy="true" />
      ) : rows.length === 0 ? (
        <div className="rounded-xl border border-line bg-surface p-10 text-center">
          <p className="font-semibold text-ink">Aucune formation ne correspond.</p>
          <p className="mt-1 text-sm text-muted">Modifiez la recherche ou les filtres, ou ajoutez une formation.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-line bg-surface">
          <table className="w-full min-w-[820px] text-left text-sm">
            <thead className="bg-surface-muted text-muted">
              <tr>
                {["Formation", "Établissement", "Niveau", "Durée", "Statut", "Dernière modification"].map((h) => (
                  <th key={h} scope="col" className="px-4 py-3 font-medium">
                    {h}
                  </th>
                ))}
                <th scope="col" className="px-4 py-3 text-right font-medium">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {rows.map((p) => (
                <tr key={p.id} className="hover:bg-surface-muted/60">
                  <td className="px-4 py-3 font-medium text-ink">{p.nom}</td>
                  <td className="px-4 py-3">
                    <SchoolBadge etablissement={p.etablissement} />
                  </td>
                  <td className="px-4 py-3 text-muted">{p.niveau}</td>
                  <td className="px-4 py-3 text-muted">{p.duree}</td>
                  <td className="px-4 py-3">
                    <StatusLabel statut={p.statut} />
                  </td>
                  <td className="px-4 py-3 text-muted">
                    {dateFormat.format(new Date(p.updatedAt))}
                    <span className="block text-xs">{p.updatedBy}</span>
                  </td>
                  <td className="px-4 py-1">
                    <div className="flex justify-end">
                      <button type="button" className={iconButton} aria-label={`Modifier ${p.nom}`} onClick={() => setEditing(p)}>
                        <AdminIcon name="edit" />
                      </button>
                      <button type="button" className={iconButton} aria-label={`Dupliquer ${p.nom}`} onClick={() => setEditing({ ...p, id: "", nom: `${p.nom} (copie)`, statut: "brouillon" })}>
                        <AdminIcon name="copy" />
                      </button>
                      <button type="button" className={iconButton} aria-label={`Supprimer ${p.nom}`} onClick={() => setToDelete(p)}>
                        <AdminIcon name="trash" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {editing !== undefined ? <ProgrammeForm initial={editing} user={user} onSave={handleSave} onClose={() => setEditing(undefined)} /> : null}

      {toDelete ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-5">
          <div role="alertdialog" aria-modal="true" aria-labelledby="suppression-titre" className="w-full max-w-md rounded-xl border border-line bg-surface p-6 shadow-float">
            <h2 id="suppression-titre" className="text-lg font-semibold text-ink">
              Supprimer cette formation ?
            </h2>
            <p className="mt-2 text-sm text-muted">
              « {toDelete.nom} » ({toDelete.etablissement}) sera retirée du catalogue. Vous pourrez annuler pendant quelques secondes.
            </p>
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="secondary" autoFocus onClick={() => setToDelete(null)}>
                Annuler
              </Button>
              <Button onClick={confirmDelete}>Supprimer</Button>
            </div>
          </div>
        </div>
      ) : null}

      <div role="status" aria-live="polite" className="pointer-events-none fixed bottom-5 left-1/2 z-50 -translate-x-1/2">
        {toast ? (
          <div className="pointer-events-auto flex items-center gap-4 rounded-lg bg-ink px-4 py-3 text-sm text-surface shadow-float">
            <span>{toast.message}</span>
            {toast.undo ? (
              <button
                type="button"
                className="font-semibold underline"
                onClick={() => {
                  toast.undo?.();
                  setToast({ message: "Suppression annulée." });
                }}
              >
                Annuler
              </button>
            ) : null}
          </div>
        ) : null}
      </div>
    </Container>
  );
}