import { type SelectHTMLAttributes, forwardRef } from "react";

import { cn } from "@/utils/cn";

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...props }, ref) => {
    return (
      <select
        ref={ref}
        className={cn(
          "flex h-10 w-full rounded-lg border border-ink-600 bg-ink-900/60 px-3 text-sm text-ink-50",
          "outline-none transition-colors focus:border-amber-glow/60 focus:ring-2 focus:ring-amber-glow/20",
          "disabled:cursor-not-allowed disabled:opacity-50",
          className,
        )}
        {...props}
      >
        {children}
      </select>
    );
  },
);
Select.displayName = "Select";
