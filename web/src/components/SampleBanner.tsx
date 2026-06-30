"use client";

interface Props {
  asOfDate: string; // "2025-10-30"
}

function monthsAgo(dateStr: string): number {
  const d = new Date(dateStr);
  const now = new Date();
  return (
    (now.getFullYear() - d.getFullYear()) * 12 +
    (now.getMonth() - d.getMonth())
  );
}

export default function SampleBanner({ asOfDate }: Props) {
  const age = monthsAgo(asOfDate);
  return (
    <div className="mb-4 px-4 py-2 bg-amber-50 border border-amber-300 rounded text-sm text-amber-800">
      <strong>Demo snapshot</strong> — data ends{" "}
      <span className="font-mono">{asOfDate}</span>{" "}
      (~{age} months old). Numbers are frozen; no live data feed.
    </div>
  );
}
