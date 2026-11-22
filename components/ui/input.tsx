import type { ComponentProps } from "react";
import { cn } from "@/lib/cn";

interface InputProps extends ComponentProps<"input"> {
  /** Libellé visible, toujours affiché (voir DESIGN.md). */
  label: string;
  /** Texte d'aide affiché sous le champ. */
  hint?: string;
  /** Message d'erreur écrit, affiché sous le champ. */
  error?: string;
}

export function Input({
  label,
  hint,
  error,
  id,
  className,
  ...props
}: InputProps) {
  const inputId = id ?? props.name;
  const hintId = hint ? `${inputId}-hint` : undefined;
  const errorId = error ? `${inputId}-error` : undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={inputId} className="text-sm font-medium text-ink">
        {label}
      </label>
      <input
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : hintId}
        className={cn(
          "h-11 w-full rounded-lg border border-line bg-surface px-3.5 text-sm text-ink transition-colors duration-150 outline-none placeholder:text-muted focus-visible:border-border-strong",
          error && "border-danger",
          className,
        )}
        {...props}
      />
      {error ? (
        <p id={errorId} className="text-xs text-danger">
          {error}
        </p>
      ) : hint ? (
        <p id={hintId} className="text-xs text-muted">
          {hint}
        </p>
      ) : null}
    </div>
  );
}
