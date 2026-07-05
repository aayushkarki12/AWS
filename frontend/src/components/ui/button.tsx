import { type ButtonHTMLAttributes, forwardRef } from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/utils/cn";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium " +
    "transition-all duration-150 active:scale-[0.97] disabled:pointer-events-none disabled:opacity-40 disabled:active:scale-100 " +
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-glow/40 focus-visible:ring-offset-2 focus-visible:ring-offset-ink-950",
  {
    variants: {
      variant: {
        primary:
          "bg-amber-glow text-ink-fixed font-semibold hover:bg-amber-deep shadow-panel-sm",
        secondary:
          "bg-ink-800 text-ink-100 border border-ink-600 hover:bg-ink-700",
        ghost: "text-ink-300 hover:bg-ink-800 hover:text-ink-100",
        danger: "bg-coral-deep text-ink-fixed-inverse hover:brightness-110",
        link: "text-amber-glow underline-offset-4 hover:underline p-0 h-auto",
      },
      size: {
        default: "h-10 px-4",
        sm: "h-8 px-3 text-[13px]",
        lg: "h-12 px-6 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(buttonVariants({ variant, size }), className)}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";
