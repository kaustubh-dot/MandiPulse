import type { Meta } from "@/lib/types";
import { Panel, SelectField, TextField, buttonClass } from "@/components/ui/primitives";

export const FARMER_PRESETS = [
  { label: "Nashik (default)", lat: 19.9975, lon: 73.78981 },
  { label: "Pune", lat: 18.5204, lon: 73.8567 },
  { label: "Aurangabad", lat: 19.8762, lon: 75.3433 },
  { label: "Solapur", lat: 17.6851, lon: 75.9064 },
  { label: "Kolhapur", lat: 16.705, lon: 74.2433 },
] as const;

export type DecisionField = "lat" | "lon" | "quantity" | "rate" | "radius";

export type DecisionDrafts = Record<DecisionField, string>;

export type DecisionErrors = Partial<Record<DecisionField, string>>;

export type CopyState = "idle" | "copied" | "failed";

export const DECISION_DEFAULTS: DecisionDrafts = {
  lat: String(FARMER_PRESETS[0].lat),
  lon: String(FARMER_PRESETS[0].lon),
  quantity: "100",
  rate: "4",
  radius: "500",
};

const FIELD_ORDER: DecisionField[] = ["lat", "lon", "quantity", "rate", "radius"];

const PARAM_FOR_FIELD: Record<DecisionField, string> = {
  lat: "lat",
  lon: "lon",
  quantity: "q",
  rate: "r",
  radius: "rad",
};

const COPY_MESSAGE: Record<CopyState, string> = {
  idle: "",
  copied: "Link copied",
  failed: "Copying failed. Copy the address from the browser bar.",
};

const COPY_TONE: Record<CopyState, string> = {
  idle: "text-transparent",
  copied: "text-success",
  failed: "text-danger",
};

type ParamsLike = { get(key: string): string | null };

export function validateDecisionInput(
  field: DecisionField,
  raw: string
): string | undefined {
  const text = raw.trim();
  if (text === "") return "Enter a number.";
  const value = Number(text);
  if (!Number.isFinite(value)) return "Enter a number.";
  switch (field) {
    case "lat":
      if (value < -90 || value > 90) {
        return "Latitude must be between \u221290 and 90 degrees.";
      }
      return undefined;
    case "lon":
      if (value < -180 || value > 180) {
        return "Longitude must be between \u2212180 and 180 degrees.";
      }
      return undefined;
    case "quantity":
      if (!(value > 0)) return "Quantity must be greater than 0 quintals.";
      return undefined;
    case "rate":
      if (value < 0) return "Transport rate cannot be negative.";
      return undefined;
    case "radius":
      if (!(value > 0)) return "Road radius must be greater than 0 km.";
      return undefined;
    default:
      return undefined;
  }
}

export function parseDecisionParams(params: ParamsLike): Partial<DecisionDrafts> {
  const drafts: Partial<DecisionDrafts> = {};
  for (const field of FIELD_ORDER) {
    const raw = params.get(PARAM_FOR_FIELD[field]);
    if (raw === null) continue;
    if (validateDecisionInput(field, raw) !== undefined) continue;
    drafts[field] = raw.trim();
  }
  return drafts;
}

export function serializeDecisionParams(
  values: Record<DecisionField, number>
): string {
  const params = new URLSearchParams();
  for (const field of FIELD_ORDER) {
    params.set(PARAM_FOR_FIELD[field], String(values[field]));
  }
  return params.toString();
}

interface Props {
  meta: Meta;
  drafts: DecisionDrafts;
  errors: DecisionErrors;
  copyState: CopyState;
  horizonDays: number;
  onChange: (field: DecisionField, value: string) => void;
  onBlurField: (field: DecisionField) => void;
  onCompare: () => void;
  onCopyLink: () => void;
}

export default function RecommendationControls({
  meta,
  drafts,
  errors,
  copyState,
  horizonDays,
  onChange,
  onBlurField,
  onCompare,
  onCopyLink,
}: Props) {
  function applyExample(value: string) {
    if (value === "") return;
    const example = FARMER_PRESETS[Number(value)];
    if (!example) return;
    onChange("lat", String(example.lat));
    onChange("lon", String(example.lon));
  }

  return (
    <Panel className="space-y-5">
      <form
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          onCompare();
        }}
        className="space-y-4"
      >
        <div>
          <h2 className="font-display text-2xl font-normal text-ink">
            Decision inputs
          </h2>
          <p className="mt-1 text-sm leading-snug text-ink-2">
            Coordinates are expert input. There is no geocoding step.
          </p>
        </div>

        <SelectField
          id="wb-example-location"
          label="Example locations"
          value=""
          onChange={applyExample}
          hint="Choosing an example fills the coordinate fields; they stay editable."
          options={[
            { value: "", label: "Fill coordinates from an example" },
            ...FARMER_PRESETS.map((preset, index) => ({
              value: String(index),
              label: preset.label,
            })),
          ]}
        />

        <div onBlur={() => onBlurField("lat")}>
          <TextField
            id="wb-lat"
            label="Latitude"
            value={drafts.lat}
            onChange={(value) => onChange("lat", value)}
            error={errors.lat}
            hint="Decimal degrees, −90 to 90."
            inputMode="decimal"
          />
        </div>

        <div onBlur={() => onBlurField("lon")}>
          <TextField
            id="wb-lon"
            label="Longitude"
            value={drafts.lon}
            onChange={(value) => onChange("lon", value)}
            error={errors.lon}
            hint="Decimal degrees, −180 to 180."
            inputMode="decimal"
          />
        </div>

        <div onBlur={() => onBlurField("quantity")}>
          <TextField
            id="wb-quantity"
            label="Quantity (quintals)"
            value={drafts.quantity}
            onChange={(value) => onChange("quantity", value)}
            error={errors.quantity}
            hint="Lot size used for the net estimate."
            inputMode="numeric"
          />
        </div>

        <div onBlur={() => onBlurField("rate")}>
          <TextField
            id="wb-rate"
            label="Transport rate (INR/km/quintal)"
            value={drafts.rate}
            onChange={(value) => onChange("rate", value)}
            error={errors.rate}
            hint="Scenario assumption, not a carrier quotation."
            inputMode="decimal"
          />
        </div>

        <div onBlur={() => onBlurField("radius")}>
          <TextField
            id="wb-radius"
            label="Maximum road radius (km)"
            value={drafts.radius}
            onChange={(value) => onChange("radius", value)}
            error={errors.radius}
            hint="Candidates beyond this estimated road distance are excluded."
            inputMode="numeric"
          />
        </div>

        <button type="submit" className={`${buttonClass.primary} w-full`}>
          Compare mandis
        </button>

        <button type="button" onClick={onCopyLink} className={`${buttonClass.secondary} w-full`}>
          Copy link
        </button>

        <p aria-live="polite" className={`min-h-5 text-xs font-bold ${COPY_TONE[copyState]}`}>
          {COPY_MESSAGE[copyState]}
        </p>
      </form>

      <div className="border-t border-rule pt-4">
        <h3 className="font-display text-xl font-normal text-ink">
          Transport assumptions
        </h3>
        <dl className="mt-2 space-y-2 text-sm">
          {[
            ["Forecast horizon", `${horizonDays}-day-ahead price target`],
            [
              "Road distance",
              `Haversine air distance \u00d7 ${meta.ranking.road_distance_factor} (estimate)`,
            ],
            ["Rate basis", "Scenario input, not a carrier quotation"],
            ["Candidate cap", `Up to ${meta.ranking.max_alternatives} alternatives shown`],
          ].map(([term, detail]) => (
            <div key={term} className="flex flex-wrap justify-between gap-x-4 gap-y-0.5">
              <dt className="text-ink-2">{term}</dt>
              <dd className="text-right text-ink">{detail}</dd>
            </div>
          ))}
        </dl>
      </div>
    </Panel>
  );
}
