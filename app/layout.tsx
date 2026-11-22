import type { Metadata } from "next";
import Script from "next/script";
import { IBM_Plex_Sans, IBM_Plex_Sans_Arabic } from "next/font/google";
import ChatWidget from "@/components/chat/chat-widget";
import { Providers } from "@/components/providers";
import Footer from "@/components/site/Footer";
import Header from "@/components/site/Header";
import PublicOnly from "@/components/site/public-only";
import { SkipToContent } from "@/components/site/skip-to-content";
import { appConfig } from "@/lib/config";
import "./globals.css";

const plex = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-plex",
});

const plexAr = IBM_Plex_Sans_Arabic({
  subsets: ["arabic"],
  weight: ["400", "500", "600"],
  variable: "--font-plex-ar",
});

export const metadata: Metadata = {
  title: {
    default: `${appConfig.name} — ${appConfig.tagline}`,
    template: `%s | ${appConfig.name}`,
  },
  description:
    "Assistant conversationnel d'orientation pour les formations de l'IIT et de l'ISB : conseil personnalisé, préinscription et suivi des candidats.",
};

/*
 * Script anti-flash : applique data-theme avant le premier rendu React.
 * cacheComponents est activé, donc pas de cookies()/headers() dans le layout.
 * Le thème est lu depuis localStorage (ou la préférence système).
 */
const themeInitScript = `
(function(){try{var s=localStorage.getItem('smartcampus-theme');var t=(s==='light'||s==='dark')?s:(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');document.documentElement.setAttribute('data-theme',t);}catch(e){}})();
`;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="fr"
      data-scroll-behavior="smooth"
      suppressHydrationWarning
      className={`${plex.variable} ${plexAr.variable} h-full antialiased`}
    >
      <Script id="theme-init" strategy="beforeInteractive">
        {themeInitScript}
      </Script>
      <body className="flex min-h-full flex-col bg-surface font-sans text-ink antialiased">
        <Providers>
          <SkipToContent />
          <PublicOnly>
            <Header />
          </PublicOnly>
          <main id="contenu" className="flex flex-1 flex-col">
            {children}
          </main>
          <PublicOnly>
            <Footer />
          </PublicOnly>
          <PublicOnly>
            <ChatWidget />
          </PublicOnly>
        </Providers>
      </body>
    </html>
  );
}