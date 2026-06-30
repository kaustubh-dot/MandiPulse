import type { BacktestSummary } from "@/lib/types";

interface Props {
  data: BacktestSummary;
}

export default function BacktestSummaryCard({ data }: Props) {
  const tiles = [
    { label: "Mean regret@1", value: `${data.mean_regret_at_1.toFixed(1)} INR/qtl` },
    {
      label: "Nearest-mandi baseline regret",
      value: `${data.nearest_mandi_baseline_regret.toFixed(1)} INR/qtl`,
    },
    {
      label: "Beats nearest mandi",
      value: `${data.pct_beats_nearest.toFixed(1)}% of dates`,
    },
  ];
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">
        Historical performance (recommendation backtest)
      </h3>
      <div className="grid grid-cols-3 gap-4 mb-2">
        {tiles.map((t) => (
          <div key={t.label} className="bg-white border border-gray-200 rounded p-3">
            <div className="text-xs text-gray-500 mb-1">{t.label}</div>
            <div className="text-lg font-semibold">{t.value}</div>
          </div>
        ))}
      </div>
      <p className="text-xs text-gray-500">
        Evaluated on {data.n_dates_evaluated} held-out test dates (
        {data.test_window_start} → {data.test_window_end}). Decision support
        only — not a guaranteed-profit signal.
      </p>
    </div>
  );
}
