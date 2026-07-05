import { type TextareaHTMLAttributes, forwardRef } from "react";

import { cn } from "@/utils/cn";

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={cn(
          "flex min-h-20 w-full rounded-lg border border-ink-600 bg-ink-900/60 px-3 py-2 text-sm text-ink-50",
          "placeholder:text-ink-400 outline-none transition-colors",
          "focus:border-amber-glow/60 focus:ring-2 focus:ring-amber-glow/20",
          "disabled:cursor-not-allowed disabled:opacity-50",
          className,
        )}
        {...props}
      />
    );
  },
);
Textarea.displayName = "Textarea";
