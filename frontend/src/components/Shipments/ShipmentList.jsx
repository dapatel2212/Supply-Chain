import React, { useState, useEffect } from 'react';
import { shipmentAPI } from '../../services/api';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, TrendingUp, Package, Clock, CheckCircle, MapIcon } from 'lucide-react';

export default function ShipmentList() {
  const navigate = useNavigate();
  const [shipments, setShipments] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');

  useEffect(() => {
    loadShipments();
  }, [filter]);

  const loadShipments = async () => {
    setLoading(true);
    try {
      const params = filter !== 'all' ? { status: filter } : {};
      const { data } = await shipmentAPI.getAll(params);
      setShipments(data.shipments || []);
      setErr('');
    } catch (e) {
      setErr('Failed to load shipments');
    } finally {
      setLoading(false);
    }
  };

  const statusColors = {
    'pending': '#f59e0b', 'registered': '#3b82f6', 'in_transit': '#8b5cf6',
    'delivered': '#10b981', 'delayed': '#ef4444', 'cancelled': '#6b7280'
  };

  const statusIcons = {
    'registered': <Package size={14} />, 'in_transit': <TrendingUp size={14} />,
    'delivered': <CheckCircle size={14} />, 'delayed': <AlertCircle size={14} />
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1>📦 Active Shipments</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          {['all', 'registered', 'in_transit', 'delivered', 'delayed'].map(s => (
            <button key={s}
              onClick={() => setFilter(s)}
              style={{
                padding: '8px 16px', borderRadius: 6, border: 'none',
                background: filter === s ? '#1e3a8a' : '#e2e8f0',
                color: filter === s ? 'white' : '#475569', cursor: 'pointer',
                textTransform: 'capitalize'
              }}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {err && <div style={{ padding: 12, background: '#fee2e2', color: '#991b1b', borderRadius: 8 }}>{err}</div>}

      {loading ? (
        <p>Loading...</p>
      ) : (
        <div style={{ display: 'grid', gap: 12 }}>
          {shipments.length ? (
            shipments.map(s => (
              <div key={s.id}
                style={{
                  background: 'white', padding: 16, borderRadius: 12, cursor: 'pointer',
                  border: `2px solid ${statusColors[s.current_status] || '#ccc'}`,
                  transition: 'box-shadow 0.2s', display: 'grid', gridTemplateColumns: '1fr auto'
                }}
              >
                <div onClick={() => navigate(`/map/${s.id}`)} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr 1fr', gap: 16 }}>
                  <div>
                    <div style={{ fontSize: 12, color: '#64748b' }}>ID</div>
                    <div style={{ fontSize: 14, fontWeight: 'bold' }}>{s.id}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 12, color: '#64748b' }}>Route</div>
                    <div style={{ fontSize: 14 }}>{s.origin_port_code} → {s.destination_port_code}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 12, color: '#64748b' }}>Status</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      {statusIcons[s.current_status]}
                      <span style={{ textTransform: 'uppercase', fontSize: 12, fontWeight: 'bold' }}>
                        {s.current_status}
                      </span>
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 12, color: '#64748b' }}>ETA</div>
                    <div style={{ fontSize: 14 }}>
                      {new Date(s.current_eta).toLocaleDateString()}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 12, color: '#64748b' }}>Progress</div>
                    <div style={{ fontSize: 14, fontWeight: 'bold', color: '#8b5cf6' }}>
                      {(['land_origin', 'sea', 'land_destination'].indexOf(s.current_phase) + 1) * 33}%
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, paddingLeft: 16 }}>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/map/${s.id}`);
                    }}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 6,
                      padding: '10px 16px', background: '#1e3a8a', color: 'white',
                      border: 'none', borderRadius: 6, cursor: 'pointer',
                      fontSize: 14, fontWeight: 'bold', whiteSpace: 'nowrap'
                    }}
                  >
                    <MapIcon size={16} /> View Map
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>
              No shipments found
            </div>
          )}
        </div>
      )}
    </div>
  );
}
