"use client";

import { Container } from "@/components/ui/container";
import { Icon } from "@/components/ui/icons";
import { useTranslation } from "@/lib/i18n";

export default function HomeContent() {
  const { dict } = useTranslation();
  const home = dict.home;

  return (
    <section className="relative flex min-h-[calc(100dvh-5rem)] items-center overflow-hidden bg-surface">
      <div
        className="pointer-events-none absolute -top-32 -right-32 h-96 w-96 rounded-full opacity-[0.07]"
        style={{ backgroundColor: "var(--iit)" }}
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute -bottom-40 -left-40 h-[28rem] w-[28rem] rounded-full opacity-[0.05]"
        style={{ backgroundColor: "var(--isb)" }}
        aria-hidden="true"
      />

      <Container className="relative z-10 py-16 md:py-24">
        <div className="max-w-2xl">
          <span className="inline-flex items-center gap-2 rounded-full border border-line bg-paper px-3.5 py-1.5 text-xs font-semibold tracking-wide text-ink">
            <span
              className="h-1.5 w-1.5 rounded-full"
              style={{ backgroundColor: "var(--iit)" }}
              aria-hidden="true"
            />
            IIT · ISB · Sfax
          </span>

          <h1 className="mt-6 text-4xl font-semibold leading-[1.1] tracking-tight text-ink md:text-5xl">
            {home.heroTitle}
          </h1>

          <p className="mt-5 text-lg leading-relaxed text-muted">
            {home.heroSubtitle}
          </p>

          <ul className="mt-8 flex flex-col gap-2.5 text-sm text-ink sm:flex-row sm:flex-wrap sm:gap-x-6">
            {home.assurances.map((item) => (
              <li key={item} className="flex items-center gap-2">
                <Icon
                  name="check"
                  size={16}
                  className="shrink-0 text-isb"
                />
                {item}
              </li>
            ))}
          </ul>

          <p className="mt-10 text-sm font-medium text-muted">
            {home.ctaHint}
          </p>
        </div>
      </Container>
    </section>
  );
}
