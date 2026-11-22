import type { ComponentProps } from "react";
import { cn } from "@/lib/cn";

/*
 * Tons du design system : iit, isb, neutral, success, warning (voir DESIGN.md).
 * Les noms hérités (default, primary, accent, violet) restent acceptés pour les
 * écrans déjà en place et pointent vers les mêmes couleurs.
 */
export type BadgeTone =
  | "iit"
  | "isb"
  | "neutral"
  | "success"
  | "warning"
  | "default"
  | "primary"
  | "accent"
  | "violet";

const toneStyles: Record<BadgeTone, string> = {
  iit: "bg-iit/10 text-iit",
  isb: "bg-isb/10 text-isb",
  neutral: "bg-surface-muted text-muted",
  success: "bg-success/10 text-success",
  warning: "bg-warning/10 text-warning",
  default: "bg-surface-muted text-muted",
  primary: "bg-iit/10 text-iit",
  accent: "bg-isb/10 text-isb",
  violet: "bg-surface-muted text-muted",
};

interface BadgeProps extends ComponentProps<"span"> {
  tone?: BadgeTone;
}

export function Badge({ tone = "neutral", className, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium",
        toneStyles[tone],
        className,
      )}
      {...props}
    />
  );
}
