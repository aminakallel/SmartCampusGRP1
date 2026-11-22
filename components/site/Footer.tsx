"use client";

import Link from "next/link";
import { buttonStyles } from "@/components/ui/button";
import { appConfig } from "@/lib/config";
import { useTranslation } from "@/lib/i18n";
import { ROUTES } from "@/lib/routes";
import { LogoMark } from "./Header";

const linkClass = "transition-colors duration-150 hover:text-ink";

export default function Footer() {
  const { t, dict } = useTranslation();
  const preinscriptionUrl = appConfig.preinscriptionUrl;

  return (
    <footer className="border-t border-line bg-paper">
      <div className="mx-auto grid max-w-6xl gap-10 px-5 py-12 md:grid-cols-[1.6fr_1fr_1fr]">
        <div>
          <div className="flex items-center gap-2 font-semibold text-ink">
            <LogoMark />
            {appConfig.name}
          </div>
          <p className="mt-3 max-w-xs text-sm text-muted">
            {t("footer.description")}
          </p>
          {preinscriptionUrl ? (
            <a
              href={preinscriptionUrl}
              target="_blank"
              rel="noopener noreferrer"
              className={buttonStyles("primary", "sm", "mt-5")}
            >
              {t("nav.preinscriptionCta")}
              <span className="sr-only"> {t("nav.opensOnFacultySite")}</span>
            </a>
          ) : null}
        </div>

        <div>
          <h2 className="text-sm font-semibold text-ink">
            {t("footer.institutions")}
          </h2>
          <ul className="mt-3 space-y-2 text-sm text-muted">
            <li>
              <span className="font-medium text-iit">IIT</span>{" "}
              {dict.footer.iitFull}
            </li>
            <li>
              <span className="font-medium text-isb">ISB</span>{" "}
              {dict.footer.isbFull}
            </li>
          </ul>
        </div>

        <div>
          <h2 className="text-sm font-semibold text-ink">{t("footer.team")}</h2>
          <ul className="mt-3 space-y-2 text-sm text-muted">
            <li>
              <Link href={ROUTES.dashboard} className={linkClass}>
                {t("footer.admissions")}
              </Link>
            </li>
          </ul>
        </div>
      </div>

      <div className="border-t border-line">
        <div className="mx-auto max-w-6xl px-5 py-4">
          <p className="text-xs text-muted">{t("footer.copyright")}</p>
        </div>
      </div>
    </footer>
  );
}
