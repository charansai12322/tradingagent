import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "./Button";

export interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Service Communication Error",
  message,
  onRetry,
  className = "",
}) => {
  return (
    <div
      role="alert"
      className={`border border-oxide/40 bg-[#A34F3F]/5 rounded-sm p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 ${className}`}
    >
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-full bg-chalk border border-oxide/30 flex items-center justify-center text-oxide flex-shrink-0 mt-0.5">
          <AlertTriangle className="w-4 h-4 stroke-[1.75]" />
        </div>
        <div>
          <h4 className="font-serif text-base text-ink font-normal tracking-tight">
            {title}
          </h4>
          <p className="text-xs text-ink/80 mt-1 font-sans leading-relaxed max-w-xl">
            {message}
          </p>
        </div>
      </div>
      {onRetry && (
        <Button
          variant="secondary"
          size="sm"
          onClick={onRetry}
          className="flex-shrink-0 border-stone hover:border-ink"
        >
          <RefreshCw className="w-3 h-3 mr-1" />
          Retry Request
        </Button>
      )}
    </div>
  );
};
