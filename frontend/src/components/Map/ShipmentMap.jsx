import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { shipmentAPI } from '../../services/api';
import { MapPin, AlertCircle, RefreshCw, Package, Clock, Navigation } from 'lucide-react';

/* global L */   // Leaflet is loaded via CDN in index.html

export default function ShipmentMap() {
  const { id } = useParams();
  const mapRef      = useRef(null);   // DOM element
  const leafletRef  = useRef(null);   // Leaflet map instance
  const markersRef  = useRef([]);     // keep track of markers to clear on update
  const polyRef     = useRef(null);

  const [shipment, setShipment]   = useState(null);
  const [events,   setEvents]     = useState([]);
  const [loading,  setLoading]    = useState(true);
  const [err,      setErr]        = useState('');
  const [refreshing, setRefreshing] = useState(false);

  // ── 1. load data ────────────────────────────────────────────────────────────
  const loadData = async (showSpinner = true) => {
    if (showSpinner) setLoading(true);
    else setRefreshing(true);
    try {
      const [shipRes, evtRes] = await Promise.all([
        shipmentAPI.getOne(id),
        shipmentAPI.getEvents(id, 30),
      ]);
      setShipment(shipRes.data.shipment);
      setEvents(evtRes.data.events || []);
      setErr('');
    } catch (e) {
      setErr('Failed to load shipment: ' + (e.response?.data?.error || e.message));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { loadData(); }, [id]);

  // ── 2. init / update Leaflet map ────────────────────────────────────────────
  useEffect(() => {
    if (!shipment || !mapRef.current) return;
    if (typeof L === 'undefined') {
      setErr('Leaflet map library not loaded. Check your internet connection.');
      return;
    }

    const {
      origin_warehouse_lat:  oLat, origin_warehouse_lng:  oLng,
      final_destination_lat: dLat, final_destination_lng: dLng,
      current_lat: cLat, current_lng: cLng,
    } = shipment;

    const hasOrigin = oLat && oLng;
    const hasDest   = dLat && dLng;
    const hasCurrent= cLat && cLng;

    if (!hasOrigin && !hasDest) return;

    const centerLat = hasOrigin ? oLat : dLat;
    const centerLng = hasOrigin ? oLng : dLng;

    // ── create map once ──────────────────────────────────────────────────────
    if (!leafletRef.current) {
      leafletRef.current = L.map(mapRef.current, {
        center: [centerLat, centerLng],
        zoom: 4,
        zoomControl: true,
        scrollWheelZoom: true,
      });

      // OpenStreetMap tiles — free, no key
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 18,
      }).addTo(leafletRef.current);
    }

    const map = leafletRef.current;

    // ── clear old markers / polyline ─────────────────────────────────────────
    markersRef.current.forEach(m => map.removeLayer(m));
    markersRef.current = [];
    if (polyRef.current) { map.removeLayer(polyRef.current); polyRef.current = null; }

    const addMarker = (lat, lng, color, emoji, title, body) => {
      const icon = L.divIcon({
        className: '',
        html: `<div style="
          background:${color};color:white;border-radius:50%;width:38px;height:38px;
          display:flex;align-items:center;justify-content:center;
          font-size:18px;border:3px solid white;
          box-shadow:0 2px 8px rgba(0,0,0,0.35);">
          ${emoji}
        </div>`,
        iconSize: [38, 38],
        iconAnchor: [19, 19],
      });
      const m = L.marker([lat, lng], { icon })
        .bindPopup(`<div style="min-width:160px;font-size:13px;">
          <strong>${title}</strong><br/>${body}
        </div>`, { closeButton: false, offset: [0, -10] })
        .addTo(map);
      markersRef.current.push(m);
      return m;
    };

    const points = [];

    if (hasOrigin) {
      addMarker(oLat, oLng, '#10b981', '🚀', '📦 Origin',
        `${shipment.origin_warehouse_city || ''}, ${shipment.origin_warehouse_country || ''}`);
      points.push([oLat, oLng]);
    }

    if (hasCurrent) {
      const m = addMarker(cLat, cLng, '#3b82f6', '📍', '🔵 Current Location',
        `Speed: ${shipment.current_speed || 0} km/h<br/>Status: ${shipment.current_status}`);
      m.openPopup();
      points.push([cLat, cLng]);
    }

    if (hasDest) {
      addMarker(dLat, dLng, '#ef4444', '🎯', '🏁 Destination',
        `${shipment.final_destination_city || ''}, ${shipment.final_destination_country || ''}`);
      points.push([dLat, dLng]);
    }

    // Draw route line
    if (points.length >= 2) {
      polyRef.current = L.polyline(points, {
        color: '#6366f1', weight: 3, opacity: 0.7, dashArray: '8 6',
      }).addTo(map);
      map.fitBounds(polyRef.current.getBounds(), { padding: [50, 50] });
    } else if (points.length === 1) {
      map.setView(points[0], 6);
    }

    // Force resize
    setTimeout(() => map.invalidateSize(), 200);
  }, [shipment]);

  // ── cleanup on unmount ───────────────────────────────────────────────────────
  useEffect(() => {
    return () => {
      if (leafletRef.current) {
        leafletRef.current.remove();
        leafletRef.current = null;
      }
    };
  }, []);

  // ── helpers ──────────────────────────────────────────────────────────────────
  const phaseInfo = {
    land_origin:      { icon: '🚚', label: 'Land (Origin → Port)' },
    sea:              { icon: '🚢', label: 'Sea Transit' },
    land_destination: { icon: '🚛', label: 'Land (Port → Destination)' },
    warehouse:        { icon: '🏭', label: 'Warehouse' },
  };

  const statusColor = (s) => ({
    registered: '#6366f1', in_transit: '#f59e0b',
    delivered: '#10b981', delayed: '#ef4444',
  })[s] || '#64748b';

  // ── render ───────────────────────────────────────────────────────────────────
  return (
    <div>
      {/* Header */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:20 }}>
        <div>
          <h1 style={{ marginBottom:4 }}>🗺️ Live Tracking — #{id}</h1>
          <p style={{ margin:0, color:'#64748b', fontSize:14 }}>
            Real-time location powered by OpenStreetMap + Leaflet
          </p>
        </div>
        <button
          onClick={() => loadData(false)}
          disabled={refreshing || loading}
          style={{
            display:'flex', alignItems:'center', gap:6, padding:'8px 18px',
            background:'#1e3a8a', color:'white', border:'none',
            borderRadius:8, cursor:'pointer', fontSize:14, fontWeight:'bold',
          }}
        >
          <RefreshCw size={15} style={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }} />
          {refreshing ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      {/* Error */}
      {err && (
        <div style={{ padding:14, background:'#fee2e2', color:'#991b1b', borderRadius:8, marginBottom:16, display:'flex', gap:8 }}>
          <AlertCircle size={20}/><span>{err}</span>
        </div>
      )}

      {loading ? (
        <div style={{ padding:60, textAlign:'center', background:'white', borderRadius:12, color:'#64748b', fontSize:16 }}>
          ⏳ Loading shipment data…
        </div>
      ) : shipment ? (
        <div style={{ display:'grid', gridTemplateColumns:'2fr 1fr', gap:16 }}>

          {/* ── MAP PANEL ─────────────────────────────────────────────────── */}
          <div style={{ background:'white', padding:20, borderRadius:12 }}>
            <h3 style={{ marginTop:0, marginBottom:14 }}>📍 Route Map</h3>

            <div
              ref={mapRef}
              id="leaflet-map"
              style={{
                height:520, borderRadius:10,
                border:'2px solid #e2e8f0',
                overflow:'hidden',
                boxShadow:'0 4px 16px rgba(0,0,0,0.08)',
              }}
            />

            {/* Legend */}
            <div style={{ display:'flex', gap:20, marginTop:14, fontSize:12, color:'#475569' }}>
              {[
                { color:'#10b981', emoji:'🚀', label:'Origin' },
                { color:'#3b82f6', emoji:'📍', label:'Current' },
                { color:'#ef4444', emoji:'🎯', label:'Destination' },
              ].map(({ color, emoji, label }) => (
                <div key={label} style={{ display:'flex', alignItems:'center', gap:6 }}>
                  <div style={{ width:14, height:14, borderRadius:'50%', background:color }}/>
                  <span>{emoji} {label}</span>
                </div>
              ))}
              <div style={{ display:'flex', alignItems:'center', gap:6 }}>
                <div style={{ width:20, height:3, background:'#6366f1', borderRadius:2,
                  backgroundImage:'repeating-linear-gradient(90deg,#6366f1 0,#6366f1 8px,transparent 8px,transparent 14px)' }}/>
                <span>Route</span>
              </div>
            </div>

            {/* Journey phases */}
            <h4 style={{ marginTop:20, marginBottom:10 }}>Journey Phases</h4>
            <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
              {['land_origin','sea','land_destination'].map(phase => {
                const active = shipment.current_phase === phase;
                const { icon, label } = phaseInfo[phase] || {};
                return (
                  <div key={phase} style={{
                    padding:'10px 14px', borderRadius:8, display:'flex', alignItems:'center', gap:14,
                    background: active ? '#eff6ff' : '#f8fafc',
                    borderLeft:`4px solid ${active ? '#3b82f6' : '#cbd5e1'}`,
                  }}>
                    <span style={{ fontSize:22 }}>{icon}</span>
                    <div>
                      <div style={{ fontWeight:'bold', fontSize:13 }}>{label}</div>
                      {phase === 'sea' && (
                        <div style={{ fontSize:11, color:'#64748b' }}>
                          {shipment.sea_distance_nm ? `${shipment.sea_distance_nm} nm` : '—'}
                        </div>
                      )}
                    </div>
                    {active && (
                      <div style={{ marginLeft:'auto', background:'#3b82f6', color:'white',
                        borderRadius:20, padding:'2px 10px', fontSize:11, fontWeight:'bold' }}>
                        ACTIVE
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Recent events */}
            <h4 style={{ marginTop:20, marginBottom:10 }}>Recent Events</h4>
            {events.length ? (
              <div style={{ display:'flex', flexDirection:'column', gap:6 }}>
                {events.slice(0, 5).map((evt, i) => (
                  <div key={i} style={{
                    padding:'10px 12px', background:'#f8fafc', borderRadius:8,
                    borderLeft:'3px solid #3b82f6', fontSize:12,
                  }}>
                    <div style={{ fontWeight:'bold', marginBottom:2 }}>{evt.event_type}</div>
                    <div style={{ color:'#64748b' }}>{evt.location_name || 'Unknown location'}</div>
                    <div style={{ fontSize:11, color:'#94a3b8', marginTop:2 }}>
                      {evt.event_timestamp ? new Date(evt.event_timestamp).toLocaleString() : 'N/A'}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color:'#94a3b8', fontSize:13 }}>No events recorded yet</p>
            )}
          </div>

          {/* ── INFO PANEL ────────────────────────────────────────────────── */}
          <div style={{ display:'flex', flexDirection:'column', gap:14 }}>

            {/* Status card */}
            <div style={{ background:'white', padding:20, borderRadius:12 }}>
              <h3 style={{ marginTop:0, marginBottom:14 }}>Shipment Info</h3>
              {[
                { label:'Shipment #',    val: shipment.shipment_number },
                { label:'Cargo Type',    val: shipment.cargo_type },
                { label:'Weight',        val: shipment.weight_tons ? `${shipment.weight_tons} tons` : '—' },
                { label:'Container #',   val: shipment.container_number || '—' },
                { label:'Vessel',        val: shipment.vessel_name || '—' },
                { label:'Current Speed', val: `${shipment.current_speed || 0} km/h` },
              ].map(({ label, val }) => (
                <div key={label} style={{ display:'flex', justifyContent:'space-between',
                  padding:'7px 0', borderBottom:'1px solid #f1f5f9', fontSize:13 }}>
                  <span style={{ color:'#64748b' }}>{label}</span>
                  <span style={{ fontWeight:'600' }}>{val}</span>
                </div>
              ))}

              {/* Status badge */}
              <div style={{ marginTop:14, textAlign:'center' }}>
                <span style={{
                  background: statusColor(shipment.current_status),
                  color:'white', borderRadius:20, padding:'6px 20px',
                  fontSize:13, fontWeight:'bold', textTransform:'uppercase',
                }}>
                  {shipment.current_status}
                </span>
              </div>
            </div>

            {/* ETA card */}
            <div style={{ background:'white', padding:20, borderRadius:12 }}>
              <h3 style={{ marginTop:0, marginBottom:14, display:'flex', alignItems:'center', gap:8 }}>
                <Clock size={18}/> ETA
              </h3>
              {[
                { label:'Initial ETA', val: shipment.initial_eta_final_delivery },
                { label:'Current ETA', val: shipment.current_eta_final_delivery },
              ].map(({ label, val }) => (
                <div key={label} style={{ marginBottom:10 }}>
                  <div style={{ fontSize:11, color:'#64748b', marginBottom:2 }}>{label}</div>
                  <div style={{ fontWeight:'bold', fontSize:14 }}>
                    {val ? new Date(val).toLocaleString() : '—'}
                  </div>
                </div>
              ))}
            </div>

            {/* Route card */}
            <div style={{ background:'white', padding:20, borderRadius:12 }}>
              <h3 style={{ marginTop:0, marginBottom:14, display:'flex', alignItems:'center', gap:8 }}>
                <Navigation size={18}/> Route
              </h3>
              <div style={{ fontSize:13 }}>
                <div style={{ marginBottom:10 }}>
                  <div style={{ color:'#64748b', fontSize:11, marginBottom:2 }}>Origin</div>
                  <div style={{ fontWeight:'bold' }}>
                    {[shipment.origin_warehouse_city, shipment.origin_warehouse_country].filter(Boolean).join(', ') || '—'}
                  </div>
                </div>
                <div style={{ textAlign:'center', color:'#6366f1', fontSize:18, margin:'6px 0' }}>↓</div>
                <div>
                  <div style={{ color:'#64748b', fontSize:11, marginBottom:2 }}>Destination</div>
                  <div style={{ fontWeight:'bold' }}>
                    {[shipment.final_destination_city, shipment.final_destination_country].filter(Boolean).join(', ') || '—'}
                  </div>
                </div>
              </div>
            </div>

            {/* Delay alert */}
            {shipment.total_delay_hours > 0 && (
              <div style={{ background:'#fef2f2', border:'2px solid #fecaca', padding:16, borderRadius:12 }}>
                <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:8 }}>
                  <AlertCircle size={18} color="#dc2626"/>
                  <strong style={{ color:'#dc2626' }}>Delay Alert</strong>
                </div>
                <p style={{ margin:0, fontSize:13, color:'#7f1d1d' }}>
                  Delayed by <strong>{shipment.total_delay_hours.toFixed(1)} hours</strong>
                </p>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div style={{ padding:40, textAlign:'center', background:'white', borderRadius:12, color:'#64748b' }}>
          Shipment not found.
        </div>
      )}

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
