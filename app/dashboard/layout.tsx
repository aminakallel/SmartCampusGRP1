"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { AdminIcon } from "@/components/admin/admin-icon";
import { LogoMark } from "@/components/site/Header";
import { logout, ROLE_LABELS, useSession } from "@/lib/admin/auth";
import { cn } from "@/lib/cn";

const NAV = [
  { href: "/dashboard", label: "Dossiers" },
  { href: "/dashboard/formations", label: "Formations" },
  { href: "/dashboard/journal", label: "Journal" },
];

function toggleTheme() {
  const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  try {
    localStorage.setItem("smartcampus-theme", next);
  } catch {
    /* stockage indisponible : le thème n'est pas mémorisé */
  }
}

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const user = useSession();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (user === null) router.replace("/connexion");
  }, [user, router]);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  if (!user) return <div className="min-h-screen bg-paper" aria-busy="true" />;

  const current = NAV.find((item) => (item.href === "/dashboard" ? pathname === item.href : pathname.startsWith(item.href)));

  return (
    <div className="min-h-screen bg-paper">
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-[264px] flex-col border-r border-line bg-surface transition-transform duration-150 lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-16 items-center gap-2 border-b border-line px-5 font-semibold text-ink">
          <LogoMark />
          SmartCampus AI
        </div>
        <nav aria-label="Espace équipe" className="flex-1 space-y-1 p-3">
          {NAV.map((item) => {
            const active = item.href === current?.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex h-11 items-center rounded-lg px-3 text-sm transition-colors duration-150",
                  active ? "bg-surface-muted font-semibold text-ink" : "text-muted hover:bg-surface-muted hover:text-ink",
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-line p-4">
          <p className="truncate text-sm font-semibold text-ink">{user.nom}</p>
          <p className="text-xs text-muted">{ROLE_LABELS[user.role]}</p>
          <button
            type="button"
            onClick={logout}
            className="mt-3 inline-flex h-11 items-center gap-2 rounded-lg px-3 text-sm text-muted transition-colors duration-150 hover:bg-surface-muted hover:text-ink"
          >
            <AdminIcon name="logout" />
            Se déconnecter
          </button>
        </div>
      </aside>

      {open ? (
        <button type="button" aria-label="Fermer le menu" onClick={() => setOpen(false)} className="fixed inset-0 z-30 bg-ink/40 lg:hidden" />
      ) : null}

      <div className="flex min-w-0 flex-col lg:pl-[264px]">
        <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-line bg-surface px-4 sm:px-6">
          <button
            type="button"
            onClick={() => setOpen(true)}
            aria-label="Ouvrir le menu"
            className="inline-flex h-11 w-11 items-center justify-center rounded-lg text-ink hover:bg-surface-muted lg:hidden"
          >
            <AdminIcon name="menu" />
          </button>
          <p className="text-sm text-muted">
            Espace équipe <span aria-hidden="true">/</span> <span className="font-semibold text-ink">{current?.label ?? "Tableau de bord"}</span>
          </p>
          <span className="ml-auto hidden rounded-full border border-line px-3 py-1 text-xs text-muted sm:inline">Données de démonstration</span>
          <button
            type="button"
            onClick={toggleTheme}
            aria-label="Changer de thème (jour ou nuit)"
            className="inline-flex h-11 w-11 items-center justify-center rounded-lg text-ink hover:bg-surface-muted"
          >
            <span className="dark:hidden">
              <AdminIcon name="moon" />
            </span>
            <span className="hidden dark:inline">
              <AdminIcon name="sun" />
            </span>
          </button>
        </header>
        <div>{children}</div>
      </div>
    </div>
  );
}