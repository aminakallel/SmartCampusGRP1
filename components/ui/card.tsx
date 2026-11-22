import type { ComponentProps } from "react";
import { cn } from "@/lib/cn";

/* Rayon 12 px, bordure 1 px, sans ombre au repos (voir DESIGN.md). */
export function Card({ className, ...props }: ComponentProps<"div">) {
  return (
    <div
      className={cn("rounded-xl border border-line bg-surface", className)}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }: ComponentProps<"div">) {
  return <div className={cn("flex flex-col gap-2 p-6", className)} {...props} />;
}

export function CardTitle({ className, ...props }: ComponentProps<"h3">) {
  return (
    <h3
      className={cn(
        "text-lg font-semibold tracking-tight text-ink",
        className,
      )}
      {...props}
    />
  );
}

export function CardDescription({ className, ...props }: ComponentProps<"p">) {
  return (
    <p
      className={cn("text-sm leading-relaxed text-muted", className)}
      {...props}
    />
  );
}

export function CardContent({ className, ...props }: ComponentProps<"div">) {
  return <div className={cn("px-6 pb-6", className)} {...props} />;
}

export function CardFooter({ className, ...props }: ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 border-t border-line px-6 py-4",
        className,
      )}
      {...props}
    />
  );
}
