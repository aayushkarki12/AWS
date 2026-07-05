import type { HTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/utils/cn";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[12px] font-medium",
  {
    variants: {
      variant: {
        neutral: "bg-ink-800 text-ink-300 border border-ink-600",
        success: "bg-teal-deep/15 text-teal-deep border border-teal-deep/30",
        warning: "bg-amber-deep/15 text-amber-deep border border-amber-deep/30",
        danger: "bg-coral-deep/15 text-coral-deep border border-coral-deep/30",
      },
    },
    defaultVariants: {
      variant: "neutral",
    },
  },
);

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
