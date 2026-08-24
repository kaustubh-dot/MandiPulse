// Market Atlas Workbench primitives.
// Small, token-driven building blocks shared by every route. Components must
// reference semantic tokens only — never raw color values.

import Link from "next/link";
import type { ReactNode } from "react";

export const SNAPSHOT_LABEL = "Snapshot 30 Oct 2025";

export function PageHeader({
  eyebrow,
  title,
  intro,
}: {
  eyebrow?: string;
  title: string;
  intro?: ReactNode;
}) {
  return (
    <header className="max-w-3xl space-y-2">
      {eyebrow ? (
        <p className="text-sm font-bold uppercase tracking-wide text-muted">{eyebrow}</p>
      ) : null}
      <h1 className="font-display text-4xl leading-[1.05] text-ink sm:text-5xl">{title}</h1>
      {intro ? <div className="text-base leading-7 text-ink-2">{intro}</div> : null}
    </header>
  );
}

export function SectionHeading({ id, children }: { id?: string; children: ReactNode }) {
  return (
    <h2
      id={id}
      className="border-b border-rule pb-2 font-display text-2xl leading-tight text-ink"
    >
      {children}
    </h2>
  );
}

export function Panel({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-panel border border-rule bg-surface p-4 ${className}`}>
      {children}
    </section>
  );
}

type NoticeTone = "info" | "warning" | "danger" | "success";

const NOTICE_TONE_STYLES: Record<NoticeTone, { border: string; label: string }> = {
  info: { border: "border-info", label: "Notice" },
  warning: { border: "border-warning", label: "Caution" },
  danger: { border: "border-danger", label: "Problem" },
  success: { border: "border-success", label: "OK" },
};

// Status is carried by text, never by color alone: each notice renders its
// tone label plus an optional explicit title.
export function StatusNotice({
  tone = "info",
  title,
  children,
  action,
}: {
  tone?: NoticeTone;
  title?: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  const styles = NOTICE_TONE_STYLES[tone];
  return (
    <div
      role={tone === "danger" ? "alert" : "status"}
      className={`rounded-panel border-l-4 bg-paper-2 p-4 ${styles.border}`}
    >
      <p className="text-xs font-bold uppercase tracking-wide text-muted">
        {title ?? styles.label}
      </p>
      <div className="mt-1 text-sm leading-relaxed text-ink-2">{children}</div>
      {action ? <div className="mt-3">{action}</div> : null}
    </div>
  );
}

export function EvidenceBlock({
  title,
  rows,
  className,
}: {
  title: string;
  rows: Array<{ label: string; value: ReactNode }>;
  className?: string;
}) {
  return (
    <div
      className={`rounded-panel border border-rule bg-paper-2 p-4${
        className ? ` ${className}` : ""
      }`}
    >
      <p className="text-xs font-bold uppercase tracking-wide text-muted">{title}</p>
      <dl className="mt-2 grid grid-cols-[minmax(9rem,auto)_1fr] gap-x-4 gap-y-1 text-sm">
        {rows.map((row) => (
          <div key={row.label} className="contents">
            <dt className="text-ink-2">{row.label}</dt>
            <dd className="numeric text-right text-ink sm:text-left">{row.value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

export function SnapshotNotice() {
  return (
    <StatusNotice tone="info" title="Data status">
      <span className="numeric">{SNAPSHOT_LABEL}</span> — frozen demonstration data.
      Figures come from a fixed offline snapshot; no live market feed is queried.
    </StatusNotice>
  );
}

export const buttonClass = {
  primary:
    "inline-flex min-h-11 items-center justify-center rounded-control bg-ink px-4 text-sm font-bold text-paper motion-safe-transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50",
  secondary:
    "inline-flex min-h-11 items-center justify-center rounded-control border border-rule-strong px-4 text-sm font-bold text-ink motion-safe-transition hover:bg-paper-2 disabled:cursor-not-allowed disabled:opacity-50",
} as const;

const inputBaseClass =
  "min-h-11 w-full rounded-control border bg-surface px-3 py-2 text-base text-ink placeholder:text-muted focus-visible:outline-2 focus-visible:outline-offset-2 motion-safe-transition";

function fieldMessageId(id: string) {
  return `${id}-message`;
}

function FieldFrame({
  id,
  label,
  hint,
  error,
  describedBy,
  children,
}: {
  id: string;
  label: string;
  hint?: string;
  error?: string;
  describedBy?: string | undefined;
  children: (ariaDescribedBy: string | undefined) => ReactNode;
}) {
  const messageId = error || hint ? fieldMessageId(id) : undefined;
  const finalDescribedBy = [describedBy, messageId].filter(Boolean).join(" ") || undefined;
  return (
    <div className="space-y-1">
      <label htmlFor={id} className="block text-sm font-bold text-ink">
        {label}
      </label>
      {hint && !error ? (
        <p id={fieldMessageId(id)} className="text-xs leading-snug text-muted">
          {hint}
        </p>
      ) : null}
      {children(finalDescribedBy)}
      {error ? (
        <p id={fieldMessageId(id)} role="alert" className="text-xs font-bold text-danger">
          {error}
        </p>
      ) : null}
    </div>
  );
}

export function TextField({
  id,
  label,
  value,
  onChange,
  hint,
  error,
  inputMode,
  autoComplete,
  describedBy,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  hint?: string;
  error?: string;
  inputMode?: "numeric" | "decimal" | "text";
  autoComplete?: string;
  describedBy?: string;
}) {
  return (
    <FieldFrame id={id} label={label} hint={hint} error={error} describedBy={describedBy}>
      {(ariaDescribedBy) => (
        <input
          id={id}
          type="text"
          inputMode={inputMode}
          autoComplete={autoComplete}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          aria-invalid={error ? true : undefined}
          aria-describedby={ariaDescribedBy}
          className={`${inputBaseClass} ${
            error ? "border-danger" : "border-rule"
          } focus-visible:outline-focus`}
        />
      )}
    </FieldFrame>
  );
}

export function SelectField({
  id,
  label,
  value,
  onChange,
  options,
  hint,
  error,
  describedBy,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
  hint?: string;
  error?: string;
  describedBy?: string;
}) {
  return (
    <FieldFrame id={id} label={label} hint={hint} error={error} describedBy={describedBy}>
      {(ariaDescribedBy) => (
        <select
          id={id}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          aria-invalid={error ? true : undefined}
          aria-describedby={ariaDescribedBy}
          className={`${inputBaseClass} ${
            error ? "border-danger" : "border-rule"
          } focus-visible:outline-focus`}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      )}
    </FieldFrame>
  );
}

export function TextLink({
  href,
  children,
}: {
  href: string;
  children: ReactNode;
}) {
  return (
    <Link href={href} className="font-bold text-info underline hover:text-ink">
      {children}
    </Link>
  );
}
