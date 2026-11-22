"use client";

import Button from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { useSession } from "@/lib/admin/auth";
import { resetDemoData, useAudit, useHydrated } from "@/lib/admin/store";

const dateFormat = new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium", timeStyle: "medium" });

export default function JournalPage() {
  const user = useSession();
  const entries = useAudit();
  const hydrated = useHydrated();

  if (!user) return null;

  function reset() {
    if (!user) return;
    if (window.confirm("Rétablir les formations de démonstration et vider le journal ?")) resetDemoData(user);
  }

  return (
    <Container className="flex flex-col gap-6 py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-ink">Journal</h1>
          <p className="mt-1 text-sm text-muted">Toutes les modifications du catalogue (500 entrées conservées au maximum).</p>
        </div>
        {user.role === "admin" ? (
          <Button variant="secondary" onClick={reset}>
            Réinitialiser les données de démonstration
          </Button>
        ) : null}
      </header>

      {!hydrated ? (
        <div className="h-48 animate-pulse rounded-xl bg-surface-muted" aria-busy="true" />
      ) : entries.length === 0 ? (
        <div className="rounded-xl border border-line bg-surface p-10 text-center">
          <p className="font-semibold text-ink">Aucune modification pour l’instant.</p>
          <p className="mt-1 text-sm text-muted">Chaque ajout, modification ou suppression de formation apparaîtra ici.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-line bg-surface">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="bg-surface-muted text-muted">
              <tr>
                {["Date", "Utilisateur", "Rôle", "Action", "Élément", "Détails"].map((h) => (
                  <th key={h} scope="col" className="px-4 py-3 font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {entries.map((e) => (
                <tr key={e.id}>
                  <td className="px-4 py-3 text-muted">{dateFormat.format(new Date(e.date))}</td>
                  <td className="px-4 py-3 text-ink">{e.user}</td>
                  <td className="px-4 py-3 text-muted">{e.role}</td>
                  <td className="px-4 py-3 font-medium text-ink">{e.action}</td>
                  <td className="px-4 py-3 text-ink">{e.item}</td>
                  <td className="px-4 py-3 text-muted">{e.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Container>
  );
}