"use client";

import { Badge } from "@/components/ui/badge";
import { Container } from "@/components/ui/container";
import { useTranslation } from "@/lib/i18n";
import DossiersDashboard from "./dossiers-dashboard";

export default function DashboardPage() {
  const { t, dict } = useTranslation();
  const dash = dict.dashboard;

  return (
    <Container className="flex flex-1 flex-col gap-8 py-10 sm:py-14">
      <header className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
            {dash.title}
          </h1>
          <Badge tone="neutral">{t("common.demoData")}</Badge>
        </div>
        <p className="max-w-2xl text-base leading-relaxed text-muted">
          {dash.subtitle}
        </p>
      </header>

      <DossiersDashboard />
    </Container>
  );
}
