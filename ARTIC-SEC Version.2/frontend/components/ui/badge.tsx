import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-sky-400 focus:ring-offset-2 select-none",
  {
    variants: {
      variant: {
        default: "border-transparent bg-sky-600 text-white shadow hover:bg-sky-500",
        secondary: "border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700",
        destructive: "border-rose-700/60 bg-rose-950/70 text-rose-300",
        warning: "border-amber-700/60 bg-amber-950/70 text-amber-300",
        success: "border-emerald-700/60 bg-emerald-950/70 text-emerald-300",
        outline: "text-slate-300 border-slate-700",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
