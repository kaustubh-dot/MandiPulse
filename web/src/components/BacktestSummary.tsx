import { EvidenceBlock } from "@/components/ui/primitives";
import { formatDateIso, formatInrPerQtl } from "@/lib/format";
import type { HonestResult } from "@/lib/types";

const MODEL_NAMES: Record<string, string> = {
  moving_average_7d: "Moving average, 7-day",
  ridge: "Ridge regression",
  lightgbm: "LightGBM",
  lightgbm_residual: "LightGBM residual",
};

function modelDisplayName(model: string): string {
  return MODEL_NAMES[model] ?? model;
}

interface Props {
  models: HonestResult[];
  nDatesEvaluated: number;
  testWindowStart: string;
  testWindowEnd: string;
}

export default function BacktestSummary({
  models,
  nDatesEvaluated,
  testWindowStart,
  testWindowEnd,
}: Props) {
  if (models.length === 0) {
    return (
      <p className="text-sm leading-relaxed text-ink-2">
        No held-out model results are present in this snapshot.
      </p>
    );
  }

  const shipped = models.find((model) => model.ships);

  return (
    <div className="space-y-3">
      <EvidenceBlock
        title="Held-out evaluation (temporal split)"
        rows={[
          ...models.map((model) => ({
            label: modelDisplayName(model.model),
            value: (
              <>
                {formatInrPerQtl(model.test_mae, 2)}
                <span
                  className={`mt-0.5 block text-xs font-bold ${
                    model.ships ? "text-success" : "text-muted"
                  }`}
                >
                  {model.ships ? "Ships" : "Not shipping"}
                </span>
              </>
            ),
          })),
          { label: "Held-out dates", value: <span className="numeric">{nDatesEvaluated}</span> },
          {
            label: "Test window",
            value: `${formatDateIso(testWindowStart)} \u2013 ${formatDateIso(testWindowEnd)}`,
          },
        ]}
      />
      <p className="text-xs leading-relaxed text-muted">
        Mean absolute error (MAE) on{" "}
        <span className="numeric">{nDatesEvaluated}</span> held-out test dates (
        {formatDateIso(testWindowStart)} to {formatDateIso(testWindowEnd)}) from a
        temporal split — every training date precedes the test window.{" "}
        {shipped
          ? `The ${modelDisplayName(shipped.model).toLowerCase()} ships because it posted the lowest held-out error; the remaining models were trained but did not beat it.`
          : "No model is marked as shipping in this snapshot."}{" "}
        Lower MAE is better.
      </p>
    </div>
  );
}
