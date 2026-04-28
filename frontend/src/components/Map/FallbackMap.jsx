// Fallback Map Component - Displays shipment route when TomTom SDK is unavailable
import React from 'react';
import { MapPin, Navigation, AlertCircle } from 'lucide-react';

export default function FallbackMap({ shipment }) {
  if (!shipment) return null;

  const originLat = shipment.origin_warehouse_lat || 0;
  const originLng = shipment.origin_warehouse_lng || 0;
  const destLat = shipment.final_destination_lat || 0;
  const destLng = shipment.final_destination_lng || 0;
  const currentLat = shipment.current_lat || (originLat + destLat) / 2;
  const currentLng = shipment.current_lng || (originLng + destLng) / 2;

  // Normalize coordinates for visualization (0-1 range)
  const minLat = Math.min(originLat, destLat, currentLat) - 1;
  const maxLat = Math.max(originLat, destLat, currentLat) + 1;
  const minLng = Math.min(originLng, destLng, currentLng) - 1;
  const maxLng = Math.max(originLng, destLng, currentLng) + 1;

  const normalizeCoord = (lat, lng) => {
    const x = ((lng - minLng) / (maxLng - minLng)) * 100;
    const y = ((lat - minLat) / (maxLat - minLat)) * 100;
    return { x, y };
  };

  const origin = normalizeCoord(originLat, originLng);
  const dest = normalizeCoord(destLat, destLng);
  const current = normalizeCoord(currentLat, currentLng);

  return (
    <div style={{
      height: 300,
      background: 'linear-gradient(135deg, #f0f4ff 0%, #e0e7ff 100%)',
      borderRadius: 8,
      border: '2px solid #dbeafe',
      marginBottom: 20,
      position: 'relative',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      padding: 16
    }}>
      <div style={{ flex: 1, position: 'relative' }}>
        {/* SVG for route visualization */}
        <svg style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0 }}>
          {/* Route line */}
          <line
            x1={`${origin.x}%`}
            y1={`${origin.y}%`}
            x2={`${dest.x}%`}
            y2={`${dest.y}%`}
            stroke="#8b5cf6"
            strokeWidth="2"
            strokeDasharray="5,5"
            opacity="0.6"
          />

          {/* Current position line to route */}
          <line
            x1={`${current.x}%`}
            y1={`${current.y}%`}
            x2={`${origin.x + (dest.x - origin.x) * 0.5}%`}
            y2={`${origin.y + (dest.y - origin.y) * 0.5}%`}
            stroke="#3b82f6"
            strokeWidth="1"
            opacity="0.4"
          />
        </svg>

        {/* Markers */}
        <div
          style={{
            position: 'absolute',
            left: `${origin.x}%`,
            top: `${origin.y}%`,
            transform: 'translate(-50%, -50%)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 4,
            zIndex: 10
          }}
        >
          <div
            style={{
              width: 24,
              height: 24,
              background: '#10b981',
              border: '3px solid white',
              borderRadius: '50%',
              boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontSize: 12
            }}
          >
            🚀
          </div>
          <div style={{ fontSize: 10, fontWeight: 'bold', background: 'white', padding: '2px 6px', borderRadius: 4, whiteSpace: 'nowrap' }}>
            Origin
          </div>
        </div>

        {/* Current location marker */}
        {(current.x !== origin.x || current.y !== origin.y) && (
          <div
            style={{
              position: 'absolute',
              left: `${current.x}%`,
              top: `${current.y}%`,
              transform: 'translate(-50%, -50%)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 4,
              zIndex: 11
            }}
          >
            <div
              style={{
                width: 20,
                height: 20,
                background: '#3b82f6',
                border: '3px solid white',
                borderRadius: '50%',
                boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
                animation: 'pulse 2s infinite',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: 10
              }}
            >
              📍
            </div>
            <div style={{ fontSize: 9, fontWeight: 'bold', background: 'white', padding: '2px 6px', borderRadius: 4, whiteSpace: 'nowrap' }}>
              Current
            </div>
          </div>
        )}

        {/* Destination marker */}
        <div
          style={{
            position: 'absolute',
            left: `${dest.x}%`,
            top: `${dest.y}%`,
            transform: 'translate(-50%, -50%)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 4,
            zIndex: 10
          }}
        >
          <div
            style={{
              width: 24,
              height: 24,
              background: '#ef4444',
              border: '3px solid white',
              borderRadius: '50%',
              boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontSize: 12
            }}
          >
            🎯
          </div>
          <div style={{ fontSize: 10, fontWeight: 'bold', background: 'white', padding: '2px 6px', borderRadius: 4, whiteSpace: 'nowrap' }}>
            Destination
          </div>
        </div>
      </div>

      {/* Legend and info */}
      <div style={{ display: 'flex', gap: 16, fontSize: 12, marginTop: 12, background: 'rgba(255,255,255,0.7)', padding: 8, borderRadius: 4 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <MapPin size={14} color="#10b981" />
          <span>{shipment.origin_warehouse_city || 'Origin'}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Navigation size={14} color="#3b82f6" />
          <span>{Math.round(shipment.sea_distance_nm || 0)} nm</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <MapPin size={14} color="#ef4444" />
          <span>{shipment.final_destination_city || 'Destination'}</span>
        </div>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
      `}</style>
    </div>
  );
}
