"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { LogoMark } from "@/components/site/Header";
import Button from "@/components/ui/button";
import { DEMO_ACCOUNTS, login, useSession } from "@/lib/admin/auth";

const field = "h-11 w-full rounded-lg border border-line bg-surface px-3 text-sm text-ink";

export default function ConnexionPage() {
  const router = useRouter();
  const user = useSession();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (user) router.replace("/dashboard/formations");
  }, [user, router]);

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!login(email, password)) {
      setError("Identifiants incorrects. Utilisez l’un des comptes de démonstration ci-dessous.");
    }
  }

  return (
    <div className="flex flex-1 items-center justify-center bg-paper px-5 py-16">
      <div className="w-full max-w-md rounded-xl border border-line bg-surface p-8">
        <div className="flex items-center gap-2 font-semibold text-ink">
          <LogoMark />
          SmartCampus AI
        </div>
        <h1 className="mt-6 text-2xl font-semibold tracking-tight text-ink">Espace équipe</h1>
        <p className="mt-2 text-sm text-muted">
          Connexion de démonstration : ceci n’est pas une authentification sécurisée.
        </p>

        <form onSubmit={submit} className="mt-6 space-y-4" noValidate>
          <div>
            <label htmlFor="email" className="mb-1 block text-sm font-medium text-ink">
              Adresse e-mail
            </label>
            <input id="email" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} className={field} />
          </div>
          <div>
            <label htmlFor="password" className="mb-1 block text-sm font-medium text-ink">
              Mot de passe
            </label>
            <input id="password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} className={field} />
          </div>
          {error ? (
            <p role="alert" className="text-sm text-danger">
              {error}
            </p>
          ) : null}
          <Button type="submit" className="w-full">
            Se connecter
          </Button>
        </form>

        <div className="mt-8 border-t border-line pt-6">
          <h2 className="text-sm font-semibold text-ink">Comptes de démonstration</h2>
          <ul className="mt-3 space-y-2">
            {DEMO_ACCOUNTS.map((account) => (
              <li key={account.email}>
                <button
                  type="button"
                  onClick={() => {
                    setEmail(account.email);
                    setPassword(account.password);
                    setError("");
                  }}
                  className="w-full rounded-lg border border-line px-3 py-2 text-left text-sm transition-colors duration-150 hover:bg-surface-muted"
                >
                  <span className="block font-medium text-ink">{account.nom}</span>
                  <span className="block text-muted">
                    {account.email} · mot de passe : {account.password}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}