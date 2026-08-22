import type { Meta } from "@/lib/types";

export const FARMER_PRESETS = [
  { label: "Nashik (default)", lat: 19.9975, lon: 73.78981 },
  { label: "Pune", lat: 18.5204, lon: 73.8567 },
  { label: "Aurangabad", lat: 19.8762, lon: 75.3433 },
  { label: "Solapur", lat: 17.6851, lon: 75.9064 },
  { label: "Kolhapur", lat: 16.705, lon: 74.2433 },
] as const;

interface Props {
  meta: Meta;
  presetIndex: number;
  onPresetIndexChange: (value: number) => void;
  quantityQtl: number;
  onQuantityChange: (value: number) => void;
  costPerKm: number;
  onCostPerKmChange: (value: number) => void;
  maxRadiusKm: number;
  onMaxRadiusChange: (value: number) => void;
}

function boundedNumber(value: string, minimum: number, maximum: number): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return minimum;
  return Math.min(maximum, Math.max(minimum, parsed));
}

export default function RecommendationControls({
  meta,
  presetIndex,
  onPresetIndexChange,
  quantityQtl,
  onQuantityChange,
  costPerKm,
  onCostPerKmChange,
  maxRadiusKm,
  onMaxRadiusChange,
}: Props) {
  const preset = FARMER_PRESETS[presetIndex] ?? FARMER_PRESETS[0];

  return (
    <fieldset className="mp-panel space-y-4">
      <legend className="px-1 text-sm font-semibold text-gray-800">Decision inputs</legend>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <label htmlFor="farmer-location" className="mb-1 block text-sm font-medium text-gray-700">
            Farmer location
          </label>
          <select
            id="farmer-location"
            className="mp-input w-full"
            value={presetIndex}
            onChange={(event) => onPresetIndexChange(Number(event.target.value))}
          >
            {FARMER_PRESETS.map((option, index) => (
              <option key={option.label} value={index}>
                {option.label}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-gray-500">
            {preset.lat.toFixed(4)}, {preset.lon.toFixed(4)}
          </p>
        </div>

        <div>
          <label htmlFor="quantity-qtl" className="mb-1 block text-sm font-medium text-gray-700">
            Quantity (quintals)
          </label>
          <input
            id="quantity-qtl"
            className="mp-input w-full"
            type="number"
            min={1}
            max={1000}
            step={1}
            inputMode="numeric"
            value={quantityQtl}
            onChange={(event) => onQuantityChange(boundedNumber(event.target.value, 1, 1000))}
          />
          <p className="mt-1 text-xs text-gray-500">Used to show the lot-level net estimate.</p>
        </div>

        <div>
          <label htmlFor="transport-cost" className="mb-1 block text-sm font-medium text-gray-700">
            Transport rate (INR/km/qtl)
          </label>
          <input
            id="transport-cost"
            className="mp-input w-full"
            type="number"
            min={0}
            max={100}
            step={0.5}
            inputMode="decimal"
            value={costPerKm}
            onChange={(event) => onCostPerKmChange(boundedNumber(event.target.value, 0, 100))}
          />
          <p className="mt-1 text-xs text-gray-500">
            Default: {meta.ranking.cost_per_km_per_quintal.toFixed(1)}
          </p>
        </div>

        <div>
          <label htmlFor="max-radius" className="mb-1 block text-sm font-medium text-gray-700">
            Maximum road radius (km)
          </label>
          <input
            id="max-radius"
            className="mp-input w-full"
            type="number"
            min={1}
            max={500}
            step={1}
            inputMode="numeric"
            value={maxRadiusKm}
            onChange={(event) => onMaxRadiusChange(boundedNumber(event.target.value, 1, 500))}
          />
          <p className="mt-1 text-xs text-gray-500">
            {meta.ranking.max_alternatives} alternatives maximum in the bundle.
          </p>
        </div>
      </div>
    </fieldset>
  );
}
