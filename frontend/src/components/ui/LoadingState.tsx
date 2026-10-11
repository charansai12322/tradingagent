import React from "react";
import { Loader2 } from "lucide-react";

export interface LoadingStateProps {
  message?: string;
  subtext?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = "Processing request...",
  subtext,
  className = "",
}) => {
  return (
    <div
      role="status"
      aria-live="polite"
      className={`py-12 px-6 flex flex-col items-center justify-center text-center bg-chalk/60 border border-stone/60 rounded-sm ${className}`}
    >
      <div className="w-8 h-8 rounded-full bg-bone border border-stone flex items-center justify-center text-ink mb-3">
        <Loader2 className="w-4 h-4 animate-spin text-ink stroke-[2]" />
      </div>
      <p className="font-serif text-base text-ink tracking-tight font-normal">
        {message}
      </p>
      {subtext && (
        <p className="text-xs text-muted font-sans mt-1 max-w-sm leading-relaxed">
          {subtext}
        </p>
      )}
    </div>
  );
};
