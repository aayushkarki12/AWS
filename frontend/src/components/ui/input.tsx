import { type InputHTMLAttributes, forwardRef } from "react";

import { cn } from "@/utils/cn";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        ref={ref}
        type={type}
        className={cn(
          "flex h-10 w-full rounded-lg border border-ink-600 bg-ink-900/60 px-3 text-sm text-ink-50",
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
Input.displayName = "Input";
