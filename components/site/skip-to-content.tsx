"use client";

import { useTranslation } from "@/lib/i18n";

export function SkipToContent() {
  const { t } = useTranslation();
  return (
    <a
      href="#contenu"
      className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-iit focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-primary-foreground"
    >
      {t("nav.skipToContent")}
    </a>
  );
}
