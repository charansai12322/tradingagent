import React from "react";
import { Loader2 } from "lucide-react";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "oxide" | "ghost";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      className = "",
      variant = "primary",
      size = "md",
      isLoading = false,
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      "inline-flex items-center justify-center font-medium transition-colors duration-150 rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink focus-visible:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed select-none";

    const variantStyles = {
      primary:
        "bg-ink text-chalk hover:bg-ink/90 border border-ink active:translate-y-[0.5px]",
      secondary:
        "bg-chalk text-ink border border-stone hover:bg-bone/80 active:translate-y-[0.5px]",
      oxide:
        "bg-oxide text-chalk hover:bg-oxide/90 border border-oxide active:translate-y-[0.5px]",
      ghost:
        "bg-transparent text-ink hover:bg-stone/30 border border-transparent",
    };

    const sizeStyles = {
      sm: "text-xs px-2.5 py-1.5 h-7 gap-1.5 font-mono",
      md: "text-sm px-4 py-2 h-9 gap-2",
      lg: "text-base px-5 py-2.5 h-11 gap-2.5",
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
        {...props}
      >
        {isLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
