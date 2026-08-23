import type { HonestResult } from "@/lib/types";

interface Props {
  results: HonestResult[];
}

export default function HonestResultsTable({ results }: Props) {
  return (
    <div
      className="overflow-x-auto rounded-panel border border-rule"
      role="region"
      aria-label="Held-out model comparison"
      tabIndex={0}
    >
      <table className="w-full min-w-[460px] border-collapse text-sm">
        <caption className="px-3 pb-2 pt-3 text-left text-xs leading-relaxed text-muted">
          Sources: reports/modeling/baseline_metrics_7d.md and
          reports/modeling/lightgbm_metrics_7d.md, committed in this repository.
          Figures are mean absolute error on the held-out test split, in INR/qtl.
        </caption>
        <thead>
          <tr className="border-b border-rule-strong text-left">
            <th
              scope="col"
              className="px-3 py-2 text-xs font-bold uppercase tracking-wide text-muted"
            >
              Model
            </th>
            <th
              scope="col"
              className="px-3 py-2 text-right text-xs font-bold uppercase tracking-wide text-muted"
            >
              Held-out test MAE (INR/qtl)
            </th>
            <th
              scope="col"
              className="px-3 py-2 text-xs font-bold uppercase tracking-wide text-muted"
            >
              Ships?
            </th>
          </tr>
        </thead>
        <tbody>
          {results.map((r) => (
            <tr key={r.model} className="border-b border-rule last:border-b-0">
              <td className="numeric px-3 py-2 text-ink">{r.model}</td>
              <td className="numeric px-3 py-2 text-right text-ink">
                {r.test_mae.toLocaleString("en-US", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </td>
              <td className="px-3 py-2">
                <span
                  className={`inline-flex items-center rounded-pill border px-2 py-1 text-xs font-bold ${
                    r.ships ? "border-success text-success" : "border-rule-strong text-muted"
                  }`}
                >
                  {r.ships ? "Ships" : "Not shipped"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
