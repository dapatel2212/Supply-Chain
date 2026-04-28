import React, { useState, useEffect } from 'react';
import { shipmentAPI } from '../../services/api';
import { Send } from 'lucide-react';

export default function RegisterShipment() {
  const [formData, setFormData] = useState({
    reference_number: '',
    shipper_name: '',
    origin_port_code: 'INMUN',
    destination_port_code: 'SGSIN',
    cargo_type: 'Electronics',
    weight_tons: 5,
    estimated_transit_days: 14,
    special_handling: ''
  });
  const [ports, setPorts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [err, setErr] = useState('');

  useEffect(() => {
    loadPorts();
  }, []);

  const loadPorts = async () => {
    try {
      const response = await shipmentAPI.getPorts();
      setPorts(response.data.ports || []);
    } catch (e) {
      console.error('Failed to load ports', e);
      // Use default ports if API fails
      setPorts([
        { code: 'INMUN', name: 'Mundra Port' },
        { code: 'INNSA', name: 'JNPT Mumbai' },
        { code: 'INMAA', name: 'Chennai Port' },
        { code: 'AEJEA', name: 'Jebel Ali' },
        { code: 'AEDXB', name: 'Port Rashid' },
        { code: 'SGSIN', name: 'Singapore Port' },
        { code: 'CNSHA', name: 'Shanghai Port' },
        { code: 'NLRTM', name: 'Rotterdam Port' },
      ]);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: ['weight_tons', 'estimated_transit_days'].includes(name) ? parseFloat(value) : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErr('');
    setSuccess('');

    try {
      const { data } = await shipmentAPI.register(formData);
      setSuccess(`✅ Shipment registered: ${data.shipment.id}`);
      setFormData({
        reference_number: '',
        shipper_name: '',
        origin_port_code: 'INMUN',
        destination_port_code: 'SGSIN',
        cargo_type: 'Electronics',
        weight_tons: 5,
        estimated_transit_days: 14,
        special_handling: ''
      });
    } catch (e) {
      setErr(e.response?.data?.error || 'Failed to register shipment');
    } finally {
      setLoading(false);
    }
  };

  const cargoTypes = ['Rice', 'Textiles', 'Electronics', 'Spices', 'Auto Parts', 'Furniture', 'Chemicals'];

  return (
    <div>
      <h1>📝 Register New Shipment</h1>
      
      <div style={{ maxWidth: 600, background: 'white', padding: 24, borderRadius: 12 }}>
        {success && <div style={{ padding: 12, background: '#dcfce7', color: '#166534', borderRadius: 6, marginBottom: 16 }}>{success}</div>}
        {err && <div style={{ padding: 12, background: '#fee2e2', color: '#991b1b', borderRadius: 6, marginBottom: 16 }}>{err}</div>}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 'bold', marginBottom: 6 }}>Reference Number *</label>
            <input name="reference_number" value={formData.reference_number} onChange={handleChange}
              style={{ width: '100%', padding: 10, borderRadius: 6, border: '1px solid #cbd5e1' }} required
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 'bold', marginBottom: 6 }}>Shipper Name *</label>
            <input name="shipper_name" value={formData.shipper_name} onChange={handleChange}
              style={{ width: '100%', padding: 10, borderRadius: 6, border: '1px solid #cbd5e1' }} required
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 'bold', marginBottom: 6 }}>Origin Port *</label>
              <select name="origin_port_code" value={formData.origin_port_code} onChange={handleChange}
                style={{ width: '100%', padding: 10, borderRadius: 6, border: '1px solid #cbd5e1' }}
              >
                {ports.map(p => <option key={p.code} value={p.code}>{p.code} - {p.name}</option>)}
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 'bold', marginBottom: 6 }}>Destination Port *</label>
              <select name="destination_port_code" value={formData.destination_port_code} onChange={handleChange}
                style={{ width: '100%', padding: 10, borderRadius: 6, border: '1px solid #cbd5e1' }}
              >
                {ports.map(p => <option key={p.code} value={p.code}>{p.code} - {p.name}</option>)}
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 12, marginBottom: 16 }}>
            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 'bold', marginBottom: 6 }}>Cargo Type *</label>
              <select name="cargo_type" value={formData.cargo_type} onChange={handleChange}
                style={{ width: '100%', padding: 10, borderRadius: 6, border: '1px solid #cbd5e1' }}
              >
                {cargoTypes.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 'bold', marginBottom: 6 }}>Weight (tons) *</label>
              <input type="number" name="weight_tons" value={formData.weight_tons} onChange={handleChange} min="0.1" step="0.1"
                style={{ width: '100%', padding: 10, borderRadius: 6, border: '1px solid #cbd5e1' }}
              />
            </div>
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 'bold', marginBottom: 6 }}>Estimated Transit (days) *</label>
            <input type="number" name="estimated_transit_days" value={formData.estimated_transit_days} onChange={handleChange} min="1" step="1"
              style={{ width: '100%', padding: 10, borderRadius: 6, border: '1px solid #cbd5e1' }}
            />
          </div>

          <div style={{ marginBottom: 20 }}>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 'bold', marginBottom: 6 }}>Special Handling</label>
            <textarea name="special_handling" value={formData.special_handling} onChange={handleChange}
              style={{ width: '100%', padding: 10, borderRadius: 6, border: '1px solid #cbd5e1', minHeight: 80 }}
              placeholder="e.g., Fragile, Keep Cool, Hazmat..."
            />
          </div>

          <button type="submit" disabled={loading}
            style={{
              width: '100%', padding: 12, background: '#1e3a8a', color: 'white',
              border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 'bold',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8
            }}
          >
            <Send size={16} /> {loading ? 'Registering...' : 'Register Shipment'}
          </button>
        </form>
      </div>
    </div>
  );
}
