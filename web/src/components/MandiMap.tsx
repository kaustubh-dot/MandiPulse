"use client";

import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { MandiMeta } from "@/lib/types";

interface Props {
  mandis: MandiMeta[];
  farmerLat?: number;
  farmerLon?: number;
  top1MarketId?: number;
}

export default function MandiMap({
  mandis,
  farmerLat,
  farmerLon,
  top1MarketId,
}: Props) {
  const centerLat = farmerLat ?? 19.7;
  const centerLon = farmerLon ?? 75.7;

  return (
    <MapContainer
      center={[centerLat, centerLon]}
      zoom={7}
      style={{ height: 380, width: "100%", borderRadius: 6 }}
      scrollWheelZoom={false}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {/* Farmer location */}
      {farmerLat != null && farmerLon != null && (
        <CircleMarker
          center={[farmerLat, farmerLon]}
          radius={8}
          pathOptions={{ color: "#1d4ed8", fillColor: "#3b82f6", fillOpacity: 0.9 }}
        >
          <Popup>Farmer location</Popup>
        </CircleMarker>
      )}

      {/* Mandi markers */}
      {mandis.map((m) => {
        const isTop1 = m.market_id === top1MarketId;
        return (
          <CircleMarker
            key={m.market_id}
            center={[m.latitude, m.longitude]}
            radius={isTop1 ? 10 : 6}
            pathOptions={{
              color: isTop1 ? "#16a34a" : "#374151",
              fillColor: isTop1 ? "#22c55e" : "#9ca3af",
              fillOpacity: 0.85,
            }}
          >
            <Popup>
              <strong>{m.market_name}</strong>
              <br />
              {m.district_name}
              <br />
              Active days: {m.active_days}
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
