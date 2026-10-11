import React from "react";

export type BadgeVariant =
  | "buy"
  | "sell"
  | "hold"
  | "positive"
  | "negative"
  | "warning"
  | "neutral"
  | "muted"
  | "oxide";

export interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: "sm" | "md";
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = "neutral",
  size = "md",
  className = "",
}) => {
  const variantStyles: Record<BadgeVariant, string> = {
    buy: "bg-[#357A52]/10 text-positive border border-positive/30 font-semibold",
    sell: "bg-[#A34F3F]/10 text-oxide border border-oxide/30 font-semibold",
    hold: "bg-stone/30 text-ink/80 border border-stone font-medium",
    positive: "bg-positive/10 text-positive border border-positive/30",
    negative: "bg-oxide/10 text-oxide border border-oxide/30",
    warning: "bg-warning/10 text-warning border border-warning/30",
    neutral: "bg-stone/20 text-ink border border-stone",
    muted: "bg-chalk text-muted border border-stone/60",
    oxide: "bg-oxide text-chalk border border-oxide",
  };

  const sizeStyles = {
    sm: "text-[10px] px-1.5 py-0.5 tracking-wider uppercase font-mono",
    md: "text-xs px-2.5 py-1 tracking-wider uppercase font-mono",
  };

  return (
    <span
      className={`inline-flex items-center justify-center rounded-sm leading-none whitespace-nowrap select-none ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};
