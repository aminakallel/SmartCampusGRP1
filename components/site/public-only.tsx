"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

/** N'affiche son contenu que sur le site public (pas sur /dashboard ni /connexion). */
export default function PublicOnly({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  if (pathname.startsWith("/dashboard") || pathname.startsWith("/connexion")) return null;
  return <>{children}</>;
}