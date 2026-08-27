// Market Atlas Workbench primitives.
// Small, token-driven building blocks shared by every route. Components must
// reference semantic tokens only - never raw color values.

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
        <p className="text-sm font-medium leading-5 text-muted">{eyebrow}</p>
      ) : null}
      <h1 className="font-display text-4xl leading-[1.05] text-ink sm:text-5xl">{title}</h1>
      {intro ? <div className="text-base leading-7 text-ink-2">{intro}</div> : null}
    </header>
  );
}

export function SectionHeading({ id, children }: { id?: string; children: ReactNode }) {
  return (
    <h2 id={id} className="border-b border-rule pb-3 font-display text-3xl font-normal leading-none text-ink">
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
    <section className={`border-y border-rule bg-transparent py-5 ${className}`}>
      {children}
    </section>
  );
}

type NoticeTone = "info" | "warning" | "danger" | "success";

const NOTICE_TONE_STYLES: Record<
  NoticeTone,
  { border: string; surface: string; label: string; title: string; text: string }
> = {
  info: {
    border: "border-info",
    surface: "bg-paper-2",
    label: "Notice",
    title: "Notice",
    text: "text-info",
  },
  warning: {
    border: "border-warning",
    surface: "bg-paper-2",
    label: "Caution",
    title: "Caution",
    text: "text-warning",
  },
  danger: {
    border: "border-danger",
    surface: "bg-paper-2",
    label: "Problem",
    title: "Problem",
    text: "text-danger",
  },
  success: {
    border: "border-success",
    surface: "bg-paper-2",
    label: "OK",
    title: "OK",
    text: "text-success",
  },
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
      className={`border-l-2 ${styles.border} ${styles.surface} p-4`}
    >
      <p className={`text-xs font-semibold leading-5 ${styles.text}`}>{title ?? styles.title}</p>
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
    <div className={`border-y border-rule py-4${className ? ` ${className}` : ""}`}>
      <p className="text-xs font-semibold leading-5 text-muted">{title}</p>
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
      <span className="numeric">{SNAPSHOT_LABEL}</span> - frozen demonstration data.
      Figures come from a fixed offline snapshot; no live market feed is queried.
    </StatusNotice>
  );
}

export const buttonClass = {
  primary:
    "inline-flex min-h-11 items-center justify-center rounded-control bg-ink px-4 text-sm font-bold text-paper whitespace-nowrap motion-safe-transition hover:opacity-90 active:translate-y-px focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus disabled:cursor-not-allowed disabled:opacity-[0.55] aria-busy:cursor-wait data-[state=error]:outline-danger data-[state=success]:outline-success",
  secondary:
    "inline-flex min-h-11 items-center justify-center rounded-control border border-rule-strong px-4 text-sm font-bold text-ink whitespace-nowrap motion-safe-transition hover:opacity-90 active:translate-y-px focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus disabled:cursor-not-allowed disabled:opacity-[0.55] aria-busy:cursor-wait data-[state=error]:outline-danger data-[state=success]:outline-success",
} as const;

type FieldState = "default" | "loading" | "success" | "error";

const inputBaseClass =
  "min-h-11 w-full rounded-control border bg-surface px-3 py-2 text-base text-ink placeholder:text-muted outline outline-1 outline-transparent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus disabled:cursor-not-allowed disabled:opacity-[0.55] motion-safe-transition";

export function fieldMessageId(id: string): string {
  return `${id}-message`;
}

function deriveFieldState({
  error,
  busy,
  valid,
}: {
  error?: string;
  busy?: boolean;
  valid?: boolean;
}): FieldState {
  return error ? "error" : busy ? "loading" : valid ? "success" : "default";
}

function fieldControlClass(state: FieldState) {
  switch (state) {
    case "error":
      return `${inputBaseClass} border-danger data-[state=error]:outline-danger`;
    case "loading":
      return `${inputBaseClass} border-warning data-[state=loading]:outline-warning`;
    case "success":
      return `${inputBaseClass} border-success data-[state=success]:outline-success`;
    default:
      return `${inputBaseClass} border-rule data-[state=default]:outline-focus`;
  }
}

function FieldFrame({
  id,
  label,
  describedBy,
  state,
  message,
  children,
}: {
  id: string;
  label: string;
  describedBy?: string | undefined;
  state: FieldState;
  message?: string;
  children: (ariaDescribedBy: string | undefined) => ReactNode;
}) {
  const messageId = fieldMessageId(id);
  const finalDescribedBy = [describedBy, messageId].filter(Boolean).join(" ") || undefined;
  return (
    <div className="space-y-1">
      <label htmlFor={id} className="block text-sm font-bold text-ink">
        {label}
      </label>
      {children(finalDescribedBy)}
      <p
        id={messageId}
        role={state === "error" ? "alert" : undefined}
        aria-live={state === "error" ? "polite" : undefined}
        className={`min-h-[1lh] text-sm leading-snug ${
          state === "error"
            ? "text-danger"
            : state === "success"
              ? "text-success"
              : "text-muted"
        }`}
      >
        {message ?? "\u00a0"}
      </p>
    </div>
  );
}

type FieldProps = {
  id: string;
  label: string;
  hint?: string;
  error?: string;
  busy?: boolean;
  valid?: boolean;
  disabled?: boolean;
  describedBy?: string;
  onBlur?: () => void;
};

export function TextField({
  id,
  label,
  value,
  onChange,
  onBlur,
  hint,
  error,
  busy,
  valid,
  disabled,
  inputMode,
  autoComplete,
  describedBy,
}: FieldProps & {
  value: string;
  onChange: (value: string) => void;
  inputMode?: "numeric" | "decimal" | "text";
  autoComplete?: string;
}) {
  const state = deriveFieldState({ error, busy, valid });
  const message = error ?? hint;
  return (
    <FieldFrame id={id} label={label} state={state} message={message} describedBy={describedBy}>
      {(ariaDescribedBy) => (
        <input
          id={id}
          type="text"
          inputMode={inputMode}
          autoComplete={autoComplete}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onBlur={onBlur}
          disabled={disabled}
          aria-busy={busy || undefined}
          aria-invalid={state === "error"}
          aria-describedby={ariaDescribedBy}
          data-state={state}
          className={fieldControlClass(state)}
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
  busy,
  valid,
  disabled,
  describedBy,
}: FieldProps & {
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
}) {
  const state = deriveFieldState({ error, busy, valid });
  const message = error ?? hint;
  return (
    <FieldFrame id={id} label={label} state={state} message={message} describedBy={describedBy}>
      {(ariaDescribedBy) => (
        <select
          id={id}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          disabled={disabled}
          aria-busy={busy || undefined}
          aria-invalid={state === "error"}
          aria-describedby={ariaDescribedBy}
          data-state={state}
          className={fieldControlClass(state)}
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
