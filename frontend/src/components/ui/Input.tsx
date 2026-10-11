import React from "react";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  mono?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, mono = false, className = "", id, ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

    return (
      <div className="w-full flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-xs font-mono tracking-wider uppercase text-muted select-none"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={`w-full bg-chalk border border-stone rounded-sm px-3 py-2 text-sm text-ink placeholder:text-muted/60 focus-visible:outline-none focus-visible:border-ink focus-visible:ring-1 focus-visible:ring-ink transition-colors ${
            mono ? "font-mono uppercase tracking-wider" : "font-sans"
          } ${error ? "border-oxide ring-1 ring-oxide" : ""} ${className}`}
          {...props}
        />
        {error && <p className="text-xs text-oxide font-sans">{error}</p>}
        {!error && hint && <p className="text-xs text-muted font-sans">{hint}</p>}
      </div>
    );
  }
);

Input.displayName = "Input";
