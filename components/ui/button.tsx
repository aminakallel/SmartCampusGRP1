import type { ComponentProps } from "react";
import { cn } from "@/lib/cn";

export type ButtonVariant = "primary" | "secondary" | "outline" | "ghost";
export type ButtonSize = "sm" | "md" | "lg";

/* Rayon 8 px, transitions 150 ms, focus géré par :focus-visible global (voir globals.css). */
const baseStyles =
  "inline-flex items-center justify-center gap-2 rounded-lg font-semibold tracking-tight transition duration-150 disabled:pointer-events-none disabled:opacity-60";

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-iit text-primary-foreground hover:brightness-110 hover:shadow-brand active:translate-y-px",
  secondary:
    "border border-line bg-surface text-ink hover:border-border-strong hover:bg-surface-muted",
  outline:
    "border border-border-strong bg-transparent text-ink hover:bg-surface-muted",
  ghost: "text-muted hover:bg-surface-muted hover:text-ink",
};

/* 44 px de hauteur minimum (voir DESIGN.md). */
const sizeStyles: Record<ButtonSize, string> = {
  sm: "h-11 px-4 text-sm",
  md: "h-11 px-5 text-sm",
  lg: "h-12 px-6 text-base",
};

/** Classes de bouton réutilisables (utile pour styler un <Link> comme un bouton). */
export function buttonStyles(
  variant: ButtonVariant = "primary",
  size: ButtonSize = "md",
  className?: string,
): string {
  return cn(baseStyles, variantStyles[variant], sizeStyles[size], className);
}

function Spinner() {
  return (
    <svg
      className="h-4 w-4 animate-spin"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <circle
        cx="12"
        cy="12"
        r="9"
        stroke="currentColor"
        strokeWidth="3"
        opacity="0.25"
      />
      <path
        d="M21 12a9 9 0 0 0-9-9"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}

interface ButtonProps extends ComponentProps<"button"> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** Affiche un indicateur et désactive le bouton pendant le traitement. */
  loading?: boolean;
}

export default function Button({
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={buttonStyles(variant, size, className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading ? <Spinner /> : null}
      {children}
    </button>
  );
}
