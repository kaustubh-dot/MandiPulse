"use client";

import { useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Tooltip, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { MandiMeta } from "@/lib/types";

const MAP_TOKEN_STYLE = `
  .leaflet-container {
    background-color: var(--mp-paper-2);
    background-image:
      linear-gradient(var(--mp-rule) 1px, transparent 1px),
      linear-gradient(90deg, var(--mp-rule) 1px, transparent 1px);
    background-size: 48px 48px;
  }
  .mp-map-farmer { stroke: var(--mp-accent-ink); stroke-width: 2.5px; fill: var(--mp-accent); fill-opacity: 0.35; }
  .mp-map-mandi { stroke: var(--mp-rule-strong); stroke-width: 1.25px; fill: var(--mp-ink-2); fill-opacity: 0.82; }
  .mp-map-top { stroke: var(--mp-ink); stroke-width: 2.5px; fill: var(--mp-accent); fill-opacity: 0.95; }
  .mp-map-label.leaflet-tooltip {
    background: var(--mp-surface-raised);
    border: 1px solid var(--mp-rule-strong);
    border-radius: 2px;
    box-shadow: none;
    color: var(--mp-ink);
    font-family: inherit;
    font-size: 11px;
    font-weight: 600;
    padding: 1px 6px;
  }
  .mp-map-label.leaflet-tooltip::before { display: none; }
  .leaflet-control-zoom { margin: 12px; }
  .leaflet-control-zoom a {
    width: 44px !important;
    height: 44px !important;
    line-height: 42px !important;
    font-size: 24px !important;
  }
`;

interface Props {
  mandis: MandiMeta[];
  farmerLat?: number;
  farmerLon?: number;
  top1MarketId?: number;
  labeledMarketIds?: number[];
  topPopupNetPrice?: string;
  topPopupRoadDistance?: string;
}

export default function MandiMap({
  mandis,
  farmerLat,
  farmerLon,
  top1MarketId,
  labeledMarketIds = [],
  topPopupNetPrice,
  topPopupRoadDistance,
}: Props) {
  const [tilesFailed, setTilesFailed] = useState(false);
  const centerLat = farmerLat ?? 19.7;
  const centerLon = farmerLon ?? 75.7;
  const labeled = new Set(labeledMarketIds);

  return (
    <div className="relative overflow-hidden rounded-panel border border-rule">
      <style>{MAP_TOKEN_STYLE}</style>
      <p className="sr-only">
        Map comparing candidate mandi locations with your location. Exact distances are listed
        in the ranked table above.
      </p>
      <MapContainer
        aria-label="Candidate mandis relative to your location"
        center={[centerLat, centerLon]}
        zoom={7}
        style={{ height: 400, width: "100%" }}
        scrollWheelZoom={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          eventHandlers={{ tileerror: () => setTilesFailed(true) }}
        />

        {farmerLat != null && farmerLon != null ? (
          <CircleMarker
            center={[farmerLat, farmerLon]}
            radius={9}
            className="mp-map-farmer"
          >
            <Tooltip direction="right" permanent className="mp-map-label">
              Your location
            </Tooltip>
            <Popup>
              <strong>Your location</strong>
              <br />
              {farmerLat.toFixed(4)}, {farmerLon.toFixed(4)}
            </Popup>
          </CircleMarker>
        ) : null}

        {mandis.map((m) => {
          const isTop1 = m.market_id === top1MarketId;
          const showLabel = isTop1 || labeled.has(m.market_id);
          return (
            <CircleMarker
              key={m.market_id}
              center={[m.latitude, m.longitude]}
              radius={isTop1 ? 11 : 6}
              className={isTop1 ? "mp-map-top" : "mp-map-mandi"}
            >
              <Tooltip
                direction="top"
                permanent={showLabel}
                className="mp-map-label"
              >
                {isTop1 ? `#1 ${m.market_name}` : m.market_name}
              </Tooltip>
              <Popup>
                <strong>{m.market_name}</strong>
                <br />
                {m.district_name}
                {isTop1 && topPopupNetPrice ? (
                  <>
                    <br />
                    Net price: {topPopupNetPrice}
                  </>
                ) : null}
                {isTop1 && topPopupRoadDistance ? (
                  <>
                    <br />
                    Road distance: {topPopupRoadDistance}
                  </>
                ) : null}
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
      {tilesFailed ? (
        <div
          role="status"
          aria-live="polite"
          aria-label="Map background unavailable"
          className="absolute inset-x-3 bottom-3 z-[500] border-y border-warning bg-paper-2 px-4 py-3 text-sm text-ink"
        >
          <strong className="font-bold">Map background unavailable.</strong>{" "}
          Candidate locations remain plotted; use the ranked table for exact distances.
        </div>
      ) : null}
    </div>
  );
}
