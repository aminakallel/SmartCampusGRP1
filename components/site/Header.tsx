"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useTheme } from "@/components/providers/theme-provider";
import { buttonStyles } from "@/components/ui/button";
import { Icon } from "@/components/ui/icons";
import { appConfig } from "@/lib/config";
import { useTranslation } from "@/lib/i18n";
import { ROUTES } from "@/lib/routes";

export function LogoMark() {
  return (
    <svg width="30" height="26" viewBox="0 0 30 26" aria-hidden="true">
      <circle cx="11" cy="13" r="10" fill="var(--color-iit)" />
      <circle cx="19" cy="13" r="10" fill="var(--color-isb)" fillOpacity="0.85" />
    </svg>
  );
}

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const { t } = useTranslation();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={isDark ? t("nav.themeLight") : t("nav.themeDark")}
      aria-pressed={isDark}
      title={isDark ? t("nav.themeLight") : t("nav.themeDark")}
      className="inline-flex h-11 w-11 items-center justify-center rounded-lg text-ink transition-colors duration-150 hover:bg-surface-muted focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
    >
      <Icon name={isDark ? "sun" : "moon"} size={20} />
    </button>
  );
}

export default function Header() {
  const { t } = useTranslation();
  const [menuOpen, setMenuOpen] = useState(false);
  const preinscriptionUrl = appConfig.preinscriptionUrl;

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setMenuOpen(false);
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-surface/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-3">
        <Link
          href={ROUTES.home}
          className="flex items-center gap-2 text-base font-semibold text-ink"
        >
          <LogoMark />
          {appConfig.name}
        </Link>

        <div className="hidden items-center gap-2 md:flex">
          <ThemeToggle />
          {preinscriptionUrl ? (
            <a
              href={preinscriptionUrl}
              target="_blank"
              rel="noopener noreferrer"
              className={buttonStyles("primary", "sm")}
            >
              {t("nav.preinscriptionCta")}
              <span className="sr-only">
                {" "}
                {t("nav.opensOnFacultySite")}
              </span>
            </a>
          ) : null}
        </div>

        <button
          type="button"
          className="inline-flex h-11 w-11 items-center justify-center rounded-lg text-ink transition-colors duration-150 hover:bg-surface-muted focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none md:hidden"
          aria-label={menuOpen ? t("nav.closeMenu") : t("nav.openMenu")}
          aria-expanded={menuOpen}
          aria-controls="mobile-menu"
          onClick={() => setMenuOpen((value) => !value)}
        >
          <Icon name={menuOpen ? "x" : "menu"} size={22} />
        </button>
      </div>

      {menuOpen ? (
        <div id="mobile-menu" className="border-t border-line bg-surface md:hidden">
          <div className="mx-auto flex max-w-6xl items-center gap-2 px-5 py-4">
            <ThemeToggle />
            {preinscriptionUrl ? (
              <a
                href={preinscriptionUrl}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => setMenuOpen(false)}
                className={buttonStyles("primary", "sm", "flex-1")}
              >
                {t("nav.preinscriptionCta")}
                <span className="sr-only">
                  {" "}
                  {t("nav.opensOnFacultySite")}
                </span>
              </a>
            ) : null}
          </div>
        </div>
      ) : null}
    </header>
  );
}
