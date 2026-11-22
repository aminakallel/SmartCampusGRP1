"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { buttonStyles } from "@/components/ui/button";
import { Icon } from "@/components/ui/icons";
import { cn } from "@/lib/cn";
import type { ReplyIntent } from "@/lib/assistant";
import { appConfig } from "@/lib/config";
import { useTranslation } from "@/lib/i18n";
import type { Programme } from "@/types";

/** Nombre de cartes affichées avant le bouton « Voir les autres formations ». */
const COLLAPSED_COUNT = 3;
/** Au-delà de ce nombre de résultats, on replie la liste. */
const COLLAPSE_THRESHOLD = 4;

interface FieldListProps {
  title: string;
  items: string[];
}

function FieldList({ title, items }: FieldListProps) {
  if (items.length === 0) return null;
  return (
    <div>
      <p className="font-medium text-ink">{title}</p>
      <ul className="mt-1 list-disc space-y-0.5 pl-4 text-muted">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

interface ProgrammeCardProps {
  programme: Programme;
  defaultOpen: boolean;
  conditionsFirst: boolean;
}

function ProgrammeCard({
  programme,
  defaultOpen,
  conditionsFirst,
}: ProgrammeCardProps) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(defaultOpen);

  const conditions = (
    <FieldList
      key="conditions"
      title={t("chat.cardConditions")}
      items={programme.prerequis}
    />
  );
  const prospects = (
    <FieldList
      key="prospects"
      title={t("chat.cardProspects")}
      items={programme.debouches}
    />
  );

  return (
    <article className="rounded-lg border border-line bg-surface">
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        className="flex w-full items-start justify-between gap-3 rounded-lg px-3 py-2.5 text-left transition-colors duration-150 hover:bg-paper focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
      >
        <span className="flex flex-col gap-1.5">
          <span className="text-sm font-semibold leading-snug text-ink">
            {programme.nom}
          </span>
          <span className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted">
            <Badge tone={programme.etablissement === "IIT" ? "iit" : "isb"}>
              {programme.etablissement}
            </Badge>
            <span>{programme.niveau}</span>
            <span aria-hidden="true">·</span>
            <span>{programme.duree}</span>
          </span>
        </span>
        <Icon
          name="chevron-up"
          size={16}
          className={cn(
            "mt-0.5 shrink-0 text-muted transition-transform duration-150",
            !open && "rotate-180",
          )}
        />
      </button>

      {open ? (
        <div className="space-y-2.5 border-t border-line px-3 py-2.5 text-xs">
          {conditionsFirst ? (
            <>
              {conditions}
              {prospects}
            </>
          ) : (
            <>
              {prospects}
              {conditions}
            </>
          )}
        </div>
      ) : null}
    </article>
  );
}

interface ChatProgrammeCardsProps {
  intent: ReplyIntent;
  programmes: Programme[];
}

/**
 * Liste de formations affichée dans le fil du chat (Prompt 3).
 * Cartes compactes dépliables ; repliées au-delà de 4 résultats ; ligne de
 * préinscription (lien externe) sous les résultats.
 */
export function ChatProgrammeCards({
  intent,
  programmes,
}: ChatProgrammeCardsProps) {
  const { t } = useTranslation();
  const [showAll, setShowAll] = useState(false);

  if (programmes.length === 0) return null;

  const shouldCollapse = programmes.length > COLLAPSE_THRESHOLD;
  const visible =
    shouldCollapse && !showAll
      ? programmes.slice(0, COLLAPSED_COUNT)
      : programmes;
  const hiddenCount = programmes.length - visible.length;

  // Les conditions d'accès ou les débouchés passent en tête et sont dépliés.
  const conditionsFirst = intent !== "prospects";
  const defaultOpen = intent === "admission" || intent === "prospects";

  return (
    <div className="flex flex-col gap-2.5">
      {visible.map((programme) => (
        <ProgrammeCard
          key={programme.id}
          programme={programme}
          defaultOpen={defaultOpen}
          conditionsFirst={conditionsFirst}
        />
      ))}

      {shouldCollapse && !showAll ? (
        <button
          type="button"
          onClick={() => setShowAll(true)}
          className={buttonStyles("secondary", "sm", "w-full")}
        >
          {t("chat.showMore")}
          <span className="text-muted">({hiddenCount})</span>
        </button>
      ) : null}

      {appConfig.preinscriptionUrl ? (
        <a
          href={appConfig.preinscriptionUrl}
          target="_blank"
          rel="noopener noreferrer"
          className={buttonStyles("primary", "sm", "w-full")}
        >
          {t("nav.preinscriptionCta")}
          <span className="sr-only">{t("nav.opensOnFacultySite")}</span>
        </a>
      ) : null}
    </div>
  );
}
