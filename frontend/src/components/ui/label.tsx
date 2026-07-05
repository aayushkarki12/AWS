import { type LabelHTMLAttributes, forwardRef } from "react";

import { cn } from "@/utils/cn";

export const Label = forwardRef<HTMLLabelElement, LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, ...props }, ref) => (
    <label
      ref={ref}
      className={cn("text-[13px] font-medium text-ink-300", className)}
      {...props}
    />
  ),
);
Label.displayName = "Label";
