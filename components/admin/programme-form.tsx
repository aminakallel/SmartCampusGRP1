"use client";

import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import Button from "@/components/ui/button";
import type { SessionUser } from "@/lib/admin/auth";
import type { ProgrammeAdmin, Statut } from "@/lib/admin/store";
import type { Etablissement, NiveauFormation } from "@/types";
import { AdminIcon } from "./admin-icon";

const NIVEAUX: NiveauFormation[] = ["Licence", "Préparatoire", "Ingénierie", "Master", "Architecture"];
const control = "h-11 w-full rounded-lg border border-line bg-surface px-3 text-sm text-ink";
const area = "w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink";

const lines = (value: string) => value.split("\n").map((s) => s.trim()).filter(Boolean);
const slugify = (value: string) =>
  value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

function Field({ id, label, hint, error, children }: { id: string; label: string; hint?: string; error?: string; children: ReactNode }) {
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-sm font-medium text-ink">
        {label}
      </label>
      {children}
      {hint && !error ? <p className="mt-1 text-xs text-muted">{hint}</p> : null}
      {error ? (
        <p id={`${id}-erreur`} className="mt-1 text-sm text-danger">
          {error}
        </p>
      ) : null}
    </div>
  );
}

interface Props {
  /** null = nouvelle formation ; un id vide = duplication. */
  initial: ProgrammeAdmin | null;
  user: SessionUser;
  onSave: (programme: ProgrammeAdmin) => void;
  onClose: () => void;
}

export default function ProgrammeForm({ initial, user, onSave, onClose }: Props) {
  const start = {
    nom: initial?.nom ?? "",
    etablissement: (initial?.etablissement ?? user.etablissement ?? "IIT") as Etablissement,
    niveau: (initial?.niveau ?? "Licence") as NiveauFormation,
    duree: initial?.duree ?? "",
    description: initial?.description ?? "",
    prerequis: (initial?.prerequis ?? []).join("\n"),
    debouches: (initial?.debouches ?? []).join("\n"),
    motsCles: (initial?.motsCles ?? []).join(", "),
    lien: initial?.lien ?? "",
    statut: (initial?.statut ?? "brouillon") as Statut,
  };
  const [v, setV] = useState(start);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const dirty = JSON.stringify(v) !== JSON.stringify(start);
  const editing = Boolean(initial?.id);

  function set<K extends keyof typeof start>(key: K, value: (typeof start)[K]) {
    setV((current) => ({ ...current, [key]: value }));
  }

  function close() {
    if (dirty && !window.confirm("Quitter sans enregistrer vos modifications ?")) return;
    onClose();
  }

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      if (dirty && !window.confirm("Quitter sans enregistrer vos modifications ?")) return;
      onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [dirty, onClose]);

  function submit(event: FormEvent) {
    event.preventDefault();
    const next: Record<string, string> = {};
    if (v.nom.trim().length < 3) next.nom = "Indiquez le nom de la formation (3 caractères minimum).";
    if (!v.duree.trim()) next.duree = "Indiquez la durée, par exemple « 3 ans ».";
    if (v.description.trim().length < 20) next.description = "La description doit contenir au moins 20 caractères.";
    setErrors(next);
    if (Object.keys(next).length > 0) return;

    const nom = v.nom.trim();
    const suffix = crypto.randomUUID().slice(0, 4);
    onSave({
      id: initial?.id || `${v.etablissement.toLowerCase()}-${slugify(nom)}-${suffix}`,
      slug: initial?.id ? initial.slug : `${slugify(nom)}-${suffix}`,
      nom,
      etablissement: v.etablissement,
      niveau: v.niveau,
      duree: v.duree.trim(),
      description: v.description.trim(),
      prerequis: lines(v.prerequis),
      debouches: lines(v.debouches),
      motsCles: v.motsCles.split(",").map((s) => s.trim()).filter(Boolean),
      lien: v.lien.trim() || undefined,
      statut: v.statut,
      updatedAt: "",
      updatedBy: "",
    });
  }

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-ink/40"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) close();
      }}
    >
      <form
        onSubmit={submit}
        noValidate
        role="dialog"
        aria-modal="true"
        aria-labelledby="form-titre"
        className="flex h-full w-full flex-col bg-surface shadow-float sm:w-[480px]"
      >
        <div className="flex items-center justify-between border-b border-line px-6 py-4">
          <h2 id="form-titre" className="text-lg font-semibold text-ink">
            {editing ? "Modifier la formation" : "Ajouter une formation"}
          </h2>
          <button type="button" onClick={close} aria-label="Fermer" className="inline-flex h-11 w-11 items-center justify-center rounded-lg text-muted hover:bg-surface-muted hover:text-ink">
            <AdminIcon name="x" />
          </button>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto px-6 py-5">
          <Field id="nom" label="Nom de la formation" error={errors.nom}>
            <input id="nom" autoFocus value={v.nom} onChange={(e) => set("nom", e.target.value)} aria-invalid={Boolean(errors.nom)} aria-describedby={errors.nom ? "nom-erreur" : undefined} className={control} />
          </Field>

          <div className="grid gap-5 sm:grid-cols-2">
            <Field id="etablissement" label="Établissement" hint={user.etablissement ? "Verrouillé selon votre rôle." : undefined}>
              <select id="etablissement" value={v.etablissement} disabled={user.etablissement !== null} onChange={(e) => set("etablissement", e.target.value as Etablissement)} className={control}>
                <option value="IIT">IIT</option>
                <option value="ISB">ISB</option>
              </select>
            </Field>
            <Field id="niveau" label="Niveau">
              <select id="niveau" value={v.niveau} onChange={(e) => set("niveau", e.target.value as NiveauFormation)} className={control}>
                {NIVEAUX.map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </Field>
          </div>

          <div className="grid gap-5 sm:grid-cols-2">
            <Field id="duree" label="Durée" error={errors.duree}>
              <input id="duree" value={v.duree} onChange={(e) => set("duree", e.target.value)} aria-invalid={Boolean(errors.duree)} aria-describedby={errors.duree ? "duree-erreur" : undefined} className={control} />
            </Field>
            <Field id="statut" label="Statut" hint="Un brouillon n’est pas visible dans le chat.">
              <select id="statut" value={v.statut} onChange={(e) => set("statut", e.target.value as Statut)} className={control}>
                <option value="brouillon">Brouillon</option>
                <option value="publiee">Publiée</option>
              </select>
            </Field>
          </div>

          <Field id="description" label="Description" error={errors.description}>
            <textarea id="description" rows={4} value={v.description} onChange={(e) => set("description", e.target.value)} aria-invalid={Boolean(errors.description)} aria-describedby={errors.description ? "description-erreur" : undefined} className={area} />
          </Field>
          <Field id="prerequis" label="Conditions d’accès" hint="Une condition par ligne.">
            <textarea id="prerequis" rows={3} value={v.prerequis} onChange={(e) => set("prerequis", e.target.value)} className={area} />
          </Field>
          <Field id="debouches" label="Débouchés" hint="Un débouché par ligne.">
            <textarea id="debouches" rows={3} value={v.debouches} onChange={(e) => set("debouches", e.target.value)} className={area} />
          </Field>
          <Field id="motsCles" label="Mots-clés" hint="Séparés par des virgules. Ils aident le chat à retrouver la formation.">
            <input id="motsCles" value={v.motsCles} onChange={(e) => set("motsCles", e.target.value)} className={control} />
          </Field>
          <Field id="lien" label="Lien officiel" hint="URL de la page de la formation sur le site de l’établissement.">
            <input id="lien" type="url" value={v.lien} onChange={(e) => set("lien", e.target.value)} className={control} />
          </Field>
        </div>

        <div className="flex justify-end gap-3 border-t border-line px-6 py-4">
          <Button type="button" variant="secondary" onClick={close}>
            Annuler
          </Button>
          <Button type="submit">Enregistrer</Button>
        </div>
      </form>
    </div>
  );
}