// Shared display formatters. Numeric evidence uses tabular figures via the
// `numeric` class; these helpers only shape values. Mirrors
// src/mandipulse/app/design.py so both surfaces render identical strings.

export const EM_DASH = "\u2014";

function isMissing(
  value: number | null | undefined
): value is null | undefined {
  return value === null || value === undefined || Number.isNaN(value);
}

function grouped(value: number | null | undefined, decimals: number): string {
  if (isMissing(value)) return EM_DASH;
  return value.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function formatInrPerQtl(
  value: number | null | undefined,
  decimals = 0
): string {
  return `${grouped(value, decimals)} INR/qtl`;
}

export function formatInr(value: number | null | undefined, decimals = 2): string {
  return `${grouped(value, decimals)} INR`;
}

export function formatKm(value: number | null | undefined, decimals = 1): string {
  return `${grouped(value, decimals)} km`;
}

export function formatPct(value: number | null | undefined, decimals = 1): string {
  if (isMissing(value)) return EM_DASH;
  return `${value.toFixed(decimals)}%`;
}

export function formatQuantity(qtl: number | null | undefined, decimals = 1): string {
  return `${grouped(qtl, decimals)} qtl`;
}

const SHORT_MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
] as const;

export function formatDateIso(iso: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (!match) return iso;
  const [, year, month, day] = match;
  const monthIndex = Number(month) - 1;
  if (monthIndex < 0 || monthIndex > 11) return iso;
  const probe = new Date(Number(year), monthIndex, Number(day));
  if (
    probe.getMonth() !== monthIndex ||
    probe.getDate() !== Number(day)
  ) {
    return iso;
  }
  return `${Number(day)} ${SHORT_MONTHS[monthIndex]} ${year}`;
}

export function formatInterval(
  lower: number | null | undefined,
  upper: number | null | undefined,
  unit = "INR/qtl",
  decimals = 0
): string {
  if (isMissing(lower) || isMissing(upper)) return EM_DASH;
  return `${grouped(lower, decimals)}\u2013${grouped(upper, decimals)} ${unit}`;
}
