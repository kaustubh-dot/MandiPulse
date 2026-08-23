import type { ReactNode } from "react";
import { StatusNotice, buttonClass } from "@/components/ui/primitives";

interface LoadingStateProps {
  label: string;
}

export function LoadingState({ label }: LoadingStateProps) {
  return (
    <div role="status" aria-live="polite" aria-busy="true" className="space-y-4">
      <span className="sr-only">{label}</span>
      <div aria-hidden="true" className="space-y-4">
        <div className="h-10 w-3/4 max-w-xs animate-pulse rounded-control bg-paper-2" />
        <div className="grid items-start gap-8 lg:grid-cols-12">
          <div className="h-64 animate-pulse rounded-panel bg-paper-2 lg:col-span-4" />
          <div className="h-96 animate-pulse rounded-panel bg-paper-2 lg:col-span-8" />
        </div>
      </div>
    </div>
  );
}

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
  hint?: ReactNode;
}

export function ErrorState({ message, onRetry, hint }: ErrorStateProps) {
  return (
    <StatusNotice tone="danger" title="Data could not be loaded">
      <p className="break-words">{message}</p>
      {hint ? <div className="mt-2">{hint}</div> : null}
      {onRetry ? (
        <button type="button" onClick={onRetry} className={`${buttonClass.secondary} mt-3`}>
          Try again
        </button>
      ) : null}
    </StatusNotice>
  );
}

interface EmptyStateProps {
  title: string;
  detail: string;
  nextAction?: ReactNode;
}

export function EmptyState({ title, detail, nextAction }: EmptyStateProps) {
  return (
    <div role="status" className="rounded-panel border border-rule bg-paper-2 p-4">
      <p className="text-xs font-bold uppercase tracking-wide text-muted">Nothing to show</p>
      <p className="mt-1 text-sm font-bold text-ink">{title}</p>
      <p className="mt-1 text-sm leading-relaxed text-ink-2">{detail}</p>
      {nextAction ? <div className="mt-3 text-sm">{nextAction}</div> : null}
    </div>
  );
}
