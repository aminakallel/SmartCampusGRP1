"use client";

import type { ReactNode } from "react";
import { LanguageProvider } from "@/lib/i18n";
import { ThemeProvider } from "./theme-provider";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <LanguageProvider>{children}</LanguageProvider>
    </ThemeProvider>
  );
}
