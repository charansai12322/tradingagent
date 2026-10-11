import React from "react";

export interface CardProps extends Omit<React.HTMLAttributes<HTMLDivElement>, "title"> {
  children: React.ReactNode;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
  badge?: React.ReactNode;
  borderAccent?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  action,
  badge,
  borderAccent = false,
  className = "",
  ...props
}) => {
  return (
    <div
      className={`bg-chalk border border-stone rounded-sm transition-all shadow-sm ${
        borderAccent ? "border-l-2 border-l-oxide" : ""
      } ${className}`}
      {...props}
    >
      {(title || subtitle || action || badge) && (
        <div className="px-5 py-3.5 border-b border-stone/80 flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              {title && (
                <h3 className="font-serif text-lg text-ink font-normal tracking-tight">
                  {title}
                </h3>
              )}
              {badge}
            </div>
            {subtitle && (
              <p className="text-xs text-muted mt-0.5 font-sans leading-relaxed">
                {subtitle}
              </p>
            )}
          </div>
          {action && <div className="flex-shrink-0">{action}</div>}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
};
