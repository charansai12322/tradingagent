import React from "react";
import { Compass } from "lucide-react";

export interface EmptyStateProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon,
  action,
  className = "",
}) => {
  return (
    <div
      className={`border border-dashed border-stone rounded-sm p-8 text-center flex flex-col items-center justify-center bg-bone/20 ${className}`}
    >
      <div className="w-9 h-9 rounded-full bg-chalk border border-stone flex items-center justify-center text-muted mb-3">
        {icon || <Compass className="w-4 h-4 stroke-[1.5]" />}
      </div>
      <h4 className="font-serif text-lg text-ink font-normal tracking-tight mb-1">
        {title}
      </h4>
      <p className="text-xs text-muted max-w-sm font-sans leading-relaxed mb-4">
        {description}
      </p>
      {action && <div>{action}</div>}
    </div>
  );
};
