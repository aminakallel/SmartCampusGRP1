"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ChatProgrammeCards } from "@/components/chat/programme-cards";
import { LogoMark } from "@/components/site/Header";
import Button from "@/components/ui/button";
import { Icon } from "@/components/ui/icons";
import {
  buildMockReply,
  type AssistantReply,
  type ReplyIntent,
} from "@/lib/assistant";
import { cn } from "@/lib/cn";
import { apiConfig } from "@/lib/config";
import { useTranslation } from "@/lib/i18n";
import type { ChatMessage } from "@/types";

/** Délai avant l'ouverture automatique sur l'accueil (voir DESIGN.md, « Mouvement »). */
const AUTO_OPEN_DELAY = 600;
/** Durée de l'indicateur de saisie avant le message d'accueil. */
const GREETING_DELAY = 800;
/** Durée de l'indicateur de saisie avant une réponse simulée. */
const REPLY_DELAY = 650;

function prefersReducedMotion(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/**
 * Chat du site (accueil centré sur le chat ; voir DESIGN.md, « Périmètre »).
 *
 * - S'ouvre automatiquement ~600 ms après l'affichage de l'accueil (animation
 *   300 ms, désactivée si prefers-reduced-motion).
 * - Desktop : panneau ancré à droite (440 px). Mobile : plein écran.
 * - Réduit : bouton flottant « Discuter » en bas à droite, avec point de
 *   notification. Échap réduit et rend le focus au bouton.
 * - Les réponses simulées (lib/assistant.ts) affichent des cartes de formations
 *   issues de lib/mock-data.ts, sans rien inventer.
 */
export default function ChatWidget() {
  const { t, dict } = useTranslation();
  const pathname = usePathname();

  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [replies, setReplies] = useState<Record<string, AssistantReply>>({});
  const [input, setInput] = useState("");
  const [isReplying, setIsReplying] = useState(false);
  const [hasGreeted, setHasGreeted] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);
  const focusInputRef = useRef(false);

  // Indicateur de saisie du message d'accueil (tant qu'aucune réponse n'existe).
  const isGreeting = isOpen && !hasGreeted;
  const isTyping = isReplying || isGreeting;

  // Ouverture automatique à l'arrivée sur l'accueil.
  useEffect(() => {
    if (pathname !== "/") return;
    const delay = prefersReducedMotion() ? 0 : AUTO_OPEN_DELAY;
    const id = window.setTimeout(() => setIsOpen(true), delay);
    return () => window.clearTimeout(id);
  }, [pathname]);

  // Message d'accueil : indicateur de saisie pendant 800 ms (une seule fois).
  useEffect(() => {
    if (!isOpen || hasGreeted) return;
    const id = window.setTimeout(() => {
      setMessages([
        {
          id: "welcome",
          role: "assistant",
          content: dict.chat.welcome,
          createdAt: new Date().toISOString(),
        },
      ]);
      setHasGreeted(true);
      setShowSuggestions(true);
    }, GREETING_DELAY);
    return () => window.clearTimeout(id);
  }, [isOpen, hasGreeted, dict.chat.welcome]);

  // Défilement vers le dernier message.
  useEffect(() => {
    if (!isOpen) return;
    bottomRef.current?.scrollIntoView({
      behavior: prefersReducedMotion() ? "auto" : "smooth",
      block: "end",
    });
  }, [messages, isReplying, isGreeting, isOpen]);

  // Focus du champ uniquement quand l'utilisateur ouvre lui-même le chat.
  useEffect(() => {
    if (isOpen && focusInputRef.current) {
      focusInputRef.current = false;
      inputRef.current?.focus();
    }
  }, [isOpen]);

  // Échap réduit le chat et rend le focus au bouton flottant.
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && isOpen) {
        setIsOpen(false);
        toggleRef.current?.focus();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  // Ouverture depuis l'ancre #chat (ROUTES.chat).
  useEffect(() => {
    function openFromHash() {
      if (window.location.hash === "#chat") {
        focusInputRef.current = true;
        setIsOpen(true);
        window.history.replaceState(null, "", window.location.pathname);
      }
    }
    openFromHash();
    window.addEventListener("hashchange", openFromHash);
    return () => window.removeEventListener("hashchange", openFromHash);
  }, []);

  function introFor(intent: ReplyIntent): string {
    switch (intent) {
      case "admission":
        return t("chat.introAdmission");
      case "prospects":
        return t("chat.introProspects");
      case "formations":
        return t("chat.introFormations");
      case "none":
        return t("chat.noMatch");
      default:
        return t("chat.introGeneral");
    }
  }

  function sendMessage(raw: string) {
    const content = raw.trim();
    if (!content || isReplying || isGreeting) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      createdAt: new Date().toISOString(),
    };

    setMessages((current) => [...current, userMessage]);
    setInput("");
    setShowSuggestions(false);
    setIsReplying(true);

    window.setTimeout(() => {
      const reply = buildMockReply(content);
      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: introFor(reply.intent),
        createdAt: new Date().toISOString(),
      };
      setMessages((current) => [...current, assistantMessage]);
      if (reply.programmes.length > 0) {
        setReplies((current) => ({ ...current, [assistantMessage.id]: reply }));
      }
      if (reply.intent === "none") setShowSuggestions(true);
      setIsReplying(false);
    }, REPLY_DELAY);
  }

  return (
    <>
      <button
        ref={toggleRef}
        type="button"
        onClick={() => {
          focusInputRef.current = true;
          setIsOpen(true);
        }}
        aria-label={t("chat.open")}
        aria-expanded={isOpen}
        aria-controls="chat-widget-panel"
        className={cn(
          "fixed right-5 bottom-5 z-50 inline-flex h-12 items-center gap-2 rounded-full bg-iit px-5 text-sm font-semibold text-primary-foreground shadow-float transition-all duration-300 hover:brightness-110 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background focus-visible:outline-none motion-reduce:transition-none sm:right-6 sm:bottom-6",
          isOpen && "pointer-events-none scale-90 opacity-0",
        )}
      >
        <Icon name="message" size={20} />
        {t("chat.discuss")}
        <span
          aria-hidden="true"
          className="absolute -top-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-background bg-isb"
        />
      </button>

      <section
        id="chat-widget-panel"
        role="dialog"
        aria-label={t("chat.title")}
        aria-modal="false"
        aria-hidden={!isOpen}
        inert={!isOpen}
        className={cn(
          "fixed z-50 flex flex-col overflow-hidden border border-line bg-surface shadow-float transition-all duration-300 ease-out motion-reduce:transition-none",
          "inset-0 h-full w-full",
          "sm:inset-auto sm:right-6 sm:bottom-6 sm:h-[min(720px,calc(100vh-3rem))] sm:w-[440px] sm:rounded-2xl",
          isOpen
            ? "translate-y-0 opacity-100"
            : "pointer-events-none translate-y-4 opacity-0 motion-reduce:translate-y-0",
        )}
      >
        <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3.5">
          <div className="flex min-w-0 items-center gap-3">
            <LogoMark />
            <div className="flex min-w-0 flex-col leading-tight">
              <span className="truncate text-sm font-semibold tracking-tight text-ink">
                {t("chat.title")}
              </span>
              <span className="inline-flex items-center gap-1.5 text-[11px] text-muted">
                <span
                  className="h-1.5 w-1.5 rounded-full bg-isb"
                  aria-hidden="true"
                />
                {t("chat.online")}
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setIsOpen(false)}
            aria-label={t("chat.minimize")}
            className="hidden h-11 w-11 shrink-0 items-center justify-center rounded-lg text-muted transition-colors duration-150 hover:bg-surface-muted hover:text-ink focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none sm:inline-flex"
          >
            <Icon name="minus" size={18} />
          </button>
          <button
            type="button"
            onClick={() => setIsOpen(false)}
            aria-label={t("chat.close")}
            className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-muted transition-colors duration-150 hover:bg-surface-muted hover:text-ink focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none sm:hidden"
          >
            <Icon name="x" size={18} />
          </button>
        </div>

        <div
          aria-live="polite"
          className="flex-1 space-y-4 overflow-y-auto px-4 py-5"
        >
          {messages.map((message) =>
            message.role === "user" ? (
              <div key={message.id} className="flex justify-end">
                <p
                  dir="auto"
                  className="max-w-[85%] rounded-2xl rounded-br-md bg-primary px-3.5 py-2.5 text-sm leading-relaxed whitespace-pre-wrap text-primary-foreground shadow-brand"
                >
                  {message.content}
                </p>
              </div>
            ) : (
              <div key={message.id} className="flex flex-col gap-2.5">
                <div className="flex items-start gap-2.5">
                  <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <Icon name="sparkles" size={15} />
                  </span>
                  <p
                    dir="auto"
                    className="max-w-[85%] rounded-2xl rounded-bl-md border border-line bg-surface-muted px-3.5 py-2.5 text-sm leading-relaxed whitespace-pre-wrap text-ink"
                  >
                    {message.content}
                  </p>
                </div>
                {replies[message.id] ? (
                  <div className="pl-[42px]">
                    <ChatProgrammeCards
                      intent={replies[message.id].intent}
                      programmes={replies[message.id].programmes}
                    />
                  </div>
                ) : null}
              </div>
            ),
          )}

          {isTyping ? (
            <div className="flex items-start gap-2.5">
              <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <Icon name="sparkles" size={15} />
              </span>
              <div
                aria-label={t("chat.isTyping")}
                className="flex items-center gap-1.5 rounded-2xl rounded-bl-md border border-line bg-surface-muted px-3.5 py-3"
              >
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted [animation-delay:0ms] motion-reduce:animate-none" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted [animation-delay:150ms] motion-reduce:animate-none" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted [animation-delay:300ms] motion-reduce:animate-none" />
              </div>
            </div>
          ) : null}

          {showSuggestions ? (
            <div className="flex flex-wrap gap-2">
              {dict.chat.suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => sendMessage(suggestion)}
                  className="rounded-full border border-line bg-background px-3 py-2 text-xs font-medium text-muted transition-colors duration-150 hover:border-border-strong hover:text-ink focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          ) : null}

          <div ref={bottomRef} />
        </div>

        <form
          onSubmit={(event) => {
            event.preventDefault();
            sendMessage(input);
          }}
          className="border-t border-line bg-surface px-3.5 py-3"
        >
          <div className="flex items-center gap-2 rounded-2xl border border-line bg-background px-2 py-1.5 transition-colors focus-within:border-border-strong focus-within:ring-2 focus-within:ring-ring/30">
            <input
              ref={inputRef}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder={t("chat.placeholder")}
              aria-label={t("chat.messageLabel")}
              className="h-11 flex-1 bg-transparent px-2 text-sm text-ink outline-none placeholder:text-muted"
            />
            <button
              type="button"
              aria-label={t("chat.voiceSoon")}
              disabled
              className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-muted transition-colors hover:bg-surface-muted disabled:opacity-50"
            >
              <Icon name="mic" size={17} />
            </button>
            <Button
              type="submit"
              size="sm"
              disabled={isTyping || input.trim().length === 0}
              aria-label={t("chat.sendMessage")}
              className="h-11 shrink-0 px-3"
            >
              <Icon name="send" size={16} />
            </Button>
          </div>
          {apiConfig.useMock ? (
            <p className="mt-2 text-[11px] text-muted">{t("chat.demoMode")}</p>
          ) : null}
        </form>
      </section>
    </>
  );
}
