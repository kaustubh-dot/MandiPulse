import type { HonestResult } from "@/lib/types";

interface Props {
  results: HonestResult[];
}

export default function HonestResultsTable({ results }: Props) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-100 text-left">
            <th className="px-3 py-2 border border-gray-200">Model</th>
            <th className="px-3 py-2 border border-gray-200 text-right">
              Test MAE (INR/qtl)
            </th>
            <th className="px-3 py-2 border border-gray-200 text-center">Ships</th>
          </tr>
        </thead>
        <tbody>
          {results.map((r) => (
            <tr
              key={r.model}
              className={r.ships ? "bg-green-50 font-medium" : ""}
            >
              <td className="px-3 py-2 border border-gray-200 font-mono text-xs">
                {r.model}
              </td>
              <td className="px-3 py-2 border border-gray-200 text-right">
                {r.test_mae.toFixed(2)}
              </td>
              <td className="px-3 py-2 border border-gray-200 text-center">
                {r.ships ? "✓" : "–"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-gray-500">
        LightGBM did not beat the 7-day moving-average baseline on the held-out
        test split. The baseline ships. This is reported transparently.
      </p>
    </div>
  );
}
