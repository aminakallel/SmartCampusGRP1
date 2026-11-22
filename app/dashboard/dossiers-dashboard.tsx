"use client";

import { useState } from "react";
import { Badge, type BadgeTone } from "@/components/ui/badge";
import Button from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Icon, type IconName } from "@/components/ui/icons";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/cn";
import { useTranslation } from "@/lib/i18n";
import type { Etablissement } from "@/types";

type Statut = "En attente" | "Préinscrit" | "Entretien planifié" | "Admis";

const STATUTS: Statut[] = [
  "En attente",
  "Préinscrit",
  "Entretien planifié",
  "Admis",
];

const STATUT_TONE: Record<Statut, BadgeTone> = {
  "En attente": "warning",
  Préinscrit: "neutral",
  "Entretien planifié": "neutral",
  Admis: "success",
};

interface Dossier {
  id: string;
  candidat: string;
  email: string;
  etablissement: Etablissement;
  formation: string;
  statut: Statut;
  misAJour: string;
}

/** Dossiers de démonstration (aucun appel backend sur cette version). */
const DOSSIERS: Dossier[] = [
  {
    id: "d-001",
    candidat: "Amine Ben Salah",
    email: "amine.bensalah@example.tn",
    etablissement: "IIT",
    formation: "Cycle Préparatoire MP",
    statut: "En attente",
    misAJour: "12 nov. 2026",
  },
  {
    id: "d-002",
    candidat: "Ines Trabelsi",
    email: "ines.trabelsi@example.tn",
    etablissement: "ISB",
    formation: "Licence en Management",
    statut: "Préinscrit",
    misAJour: "11 nov. 2026",
  },
  {
    id: "d-003",
    candidat: "Youssef Khelifi",
    email: "youssef.khelifi@example.tn",
    etablissement: "IIT",
    formation: "Cycle Ingénieur Informatique",
    statut: "Entretien planifié",
    misAJour: "10 nov. 2026",
  },
  {
    id: "d-004",
    candidat: "Salma Gharbi",
    email: "salma.gharbi@example.tn",
    etablissement: "ISB",
    formation: "Cycle Ingénieur en Management",
    statut: "Admis",
    misAJour: "09 nov. 2026",
  },
  {
    id: "d-005",
    candidat: "Mehdi Bouazizi",
    email: "mehdi.bouazizi@example.tn",
    etablissement: "IIT",
    formation: "Licence en Sciences de l’Informatique",
    statut: "Préinscrit",
    misAJour: "08 nov. 2026",
  },
  {
    id: "d-006",
    candidat: "Nour Jaziri",
    email: "nour.jaziri@example.tn",
    etablissement: "ISB",
    formation: "Licence en Management",
    statut: "En attente",
    misAJour: "08 nov. 2026",
  },
  {
    id: "d-007",
    candidat: "Rania Hamdi",
    email: "rania.hamdi@example.tn",
    etablissement: "IIT",
    formation: "Cycle Ingénieur Génie Électrique",
    statut: "Entretien planifié",
    misAJour: "07 nov. 2026",
  },
  {
    id: "d-008",
    candidat: "Karim Zouari",
    email: "karim.zouari@example.tn",
    etablissement: "IIT",
    formation: "Cycle Préparatoire MP",
    statut: "Admis",
    misAJour: "05 nov. 2026",
  },
  {
    id: "d-009",
    candidat: "Emna Chaabane",
    email: "emna.chaabane@example.tn",
    etablissement: "ISB",
    formation: "Cycle Ingénieur en Management",
    statut: "Préinscrit",
    misAJour: "04 nov. 2026",
  },
  {
    id: "d-010",
    candidat: "Hedi Mansouri",
    email: "hedi.mansouri@example.tn",
    etablissement: "IIT",
    formation: "Licence en Sciences de l’Informatique",
    statut: "En attente",
    misAJour: "03 nov. 2026",
  },
];

type FiltreEtablissement = "tous" | Etablissement;

export default function DossiersDashboard() {
  const { dict } = useTranslation();
  const dash = dict.dashboard;

  const INDICATEURS: { icon: IconName; label: string; valeur: number }[] = [
    { icon: "users", label: dash.indicators.tracked, valeur: DOSSIERS.length },
    {
      icon: "clock",
      label: dash.indicators.pending,
      valeur: DOSSIERS.filter((dossier) => dossier.statut === "En attente").length,
    },
    {
      icon: "calendar-check",
      label: dash.indicators.interviews,
      valeur: DOSSIERS.filter(
        (dossier) => dossier.statut === "Entretien planifié",
      ).length,
    },
    {
      icon: "check",
      label: dash.indicators.admitted,
      valeur: DOSSIERS.filter((dossier) => dossier.statut === "Admis").length,
    },
  ];

  const STATUT_LABEL: Record<Statut, string> = {
    "En attente": dash.statuses.pending,
    Préinscrit: dash.statuses.preinscribed,
    "Entretien planifié": dash.statuses.interview,
    Admis: dash.statuses.admitted,
  };

  const [recherche, setRecherche] = useState("");
  const [statut, setStatut] = useState<Statut | "tous">("tous");
  const [etablissement, setEtablissement] =
    useState<FiltreEtablissement>("tous");

  const terme = recherche.trim().toLowerCase();
  const dossiers = DOSSIERS.filter((dossier) => {
    const correspondEtablissement =
      etablissement === "tous" || dossier.etablissement === etablissement;
    const correspondStatut = statut === "tous" || dossier.statut === statut;
    const correspondRecherche =
      terme.length === 0 ||
      dossier.candidat.toLowerCase().includes(terme) ||
      dossier.email.toLowerCase().includes(terme);
    return correspondEtablissement && correspondStatut && correspondRecherche;
  });

  const filtresActifs =
    terme.length > 0 || statut !== "tous" || etablissement !== "tous";

  function reinitialiser() {
    setRecherche("");
    setStatut("tous");
    setEtablissement("tous");
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {INDICATEURS.map((indicateur) => (
          <Card
            key={indicateur.label}
            className="flex items-center gap-3 p-4"
          >
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-paper text-iit">
              <Icon name={indicateur.icon} size={18} />
            </span>
            <div>
              <p className="text-2xl font-semibold leading-none text-ink">
                {indicateur.valeur}
              </p>
              <p className="mt-1 text-xs text-muted">{indicateur.label}</p>
            </div>
          </Card>
        ))}
      </div>

      <div className="flex flex-col gap-5 rounded-xl border border-line bg-surface p-5">
        <div className="grid gap-5 sm:grid-cols-2">
          <Input
            name="recherche"
            label={dash.searchLabel}
            hint={dash.searchHint}
            placeholder={dash.searchPlaceholder}
            value={recherche}
            onChange={(event) => setRecherche(event.target.value)}
          />
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="filtre-statut"
              className="text-sm font-medium text-ink"
            >
              {dash.statusLabel}
            </label>
            <select
              id="filtre-statut"
              value={statut}
              onChange={(event) =>
                setStatut(event.target.value as Statut | "tous")
              }
              className="h-11 w-full rounded-lg border border-line bg-surface px-3.5 text-sm text-ink transition-colors duration-150 outline-none focus-visible:border-border-strong"
            >
              <option value="tous">{dash.allStatuses}</option>
              {STATUTS.map((option) => (
                <option key={option} value={option}>
                  {STATUT_LABEL[option]}
                </option>
              ))}
            </select>
            <p className="text-xs text-muted">
              {dash.statusHint}
            </p>
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <span id="filtre-etablissement" className="text-sm font-medium text-ink">
            {dash.establishmentLabel}
          </span>
          <div
            role="radiogroup"
            aria-labelledby="filtre-etablissement"
            className="inline-flex w-fit rounded-lg border border-line bg-paper p-1"
          >
            {(["tous", "IIT", "ISB"] as const).map((code) => (
              <label
                key={code}
                className={cn(
                  "cursor-pointer rounded-md px-4 py-2 text-sm font-medium transition-colors duration-150",
                  etablissement === code
                    ? "bg-surface text-ink shadow-card"
                    : "text-muted hover:text-ink",
                )}
              >
                <input
                  type="radio"
                  name="filtre-etablissement"
                  value={code}
                  checked={etablissement === code}
                  onChange={() => setEtablissement(code)}
                  className="sr-only"
                />
                {code === "tous" ? dash.allEstablishments : code}
              </label>
            ))}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p aria-live="polite" className="text-sm text-muted">
          {dash.resultsCount(dossiers.length, DOSSIERS.length)}
        </p>
        {filtresActifs ? (
          <Button variant="ghost" size="sm" onClick={reinitialiser}>
            {dash.resetFilters}
          </Button>
        ) : null}
      </div>

      {dossiers.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-border-strong bg-surface px-6 py-12 text-center">
          <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-paper text-muted">
            <Icon name="search" size={20} />
          </span>
          <p className="text-sm font-medium text-ink">
            {dash.emptyTitle}
          </p>
          <p className="max-w-sm text-sm leading-relaxed text-muted">
            {dash.emptyText}
          </p>
          <Button variant="secondary" size="sm" onClick={reinitialiser}>
            {dash.resetFilters}
          </Button>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-line bg-surface">
          <table className="w-full min-w-[720px] border-collapse text-sm">
            <caption className="sr-only">
              {dash.tableCaption}
            </caption>
            <thead>
              <tr className="border-b border-line text-left text-xs font-semibold text-muted">
                <th scope="col" className="px-4 py-3">
                  {dash.columns.candidate}
                </th>
                <th scope="col" className="px-4 py-3">
                  {dash.columns.establishment}
                </th>
                <th scope="col" className="px-4 py-3">
                  {dash.columns.formation}
                </th>
                <th scope="col" className="px-4 py-3">
                  {dash.columns.status}
                </th>
                <th scope="col" className="px-4 py-3">
                  {dash.columns.updated}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {dossiers.map((dossier) => (
                <tr
                  key={dossier.id}
                  className="transition-colors duration-150 hover:bg-paper"
                >
                  <th
                    scope="row"
                    className="px-4 py-3 text-left font-medium text-ink"
                  >
                    {dossier.candidat}
                    <span className="mt-0.5 block text-xs font-normal text-muted">
                      {dossier.email}
                    </span>
                  </th>
                  <td className="px-4 py-3">
                    <Badge
                      tone={dossier.etablissement === "IIT" ? "iit" : "isb"}
                    >
                      {dossier.etablissement}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-muted">{dossier.formation}</td>
                  <td className="px-4 py-3">
                    <Badge tone={STATUT_TONE[dossier.statut]}>
                      {STATUT_LABEL[dossier.statut]}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-muted">
                    {dossier.misAJour}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
