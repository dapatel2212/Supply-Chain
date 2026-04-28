import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useNavigate } from 'react-router-dom';
import { authAPI } from './services/api';
import ShipmentList from './components/Shipments/ShipmentList';
import RegisterShipment from './components/Shipments/RegisterShipment';
import Analytics from './components/Analytics/Analytics';
import ShipmentMap from './components/Map/ShipmentMap';
import { Ship, BarChart3, Plus, LogOut, Map } from 'lucide-react';

function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('raj@exporters.in');
  const [password, setPassword] = useState('password123');
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErr('');
    try {
      const { data } = await authAPI.login(email, password);
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      navigate('/shipments');
    } catch (e) {
      setErr('Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%)'
    }}>
      <div style={{ background: 'white', padding: 40, borderRadius: 16, width: 400, boxShadow: '0 20px 50px rgba(0,0,0,0.3)' }}>
        <div style={{ textAlign: 'center', marginBottom: 30 }}>
          <Ship size={48} color="#1e3a8a" />
          <h1 style={{ color: '#1e3a8a', marginTop: 10 }}>ShipTrack AI</h1>
          <p style={{ color: '#64748b', fontSize: 14 }}>Smart Logistics Tracking</p>
        </div>
        <form onSubmit={submit}>
          <input
            type="email" value={email} onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            style={{ width: '100%', padding: 12, marginBottom: 12, borderRadius: 8, border: '1px solid #cbd5e1' }}
          />
          <input
            type="password" value={password} onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            style={{ width: '100%', padding: 12, marginBottom: 12, borderRadius: 8, border: '1px solid #cbd5e1' }}
          />
          {err && <div style={{ color: '#dc2626', marginBottom: 12, fontSize: 14 }}>{err}</div>}
          <button
            type="submit" disabled={loading}
            style={{
              width: '100%', padding: 12, background: '#1e3a8a', color: 'white',
              border: 'none', borderRadius: 8, fontSize: 16, cursor: 'pointer'
            }}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <div style={{ marginTop: 20, padding: 12, background: '#f1f5f9', borderRadius: 8, fontSize: 12, color: '#475569' }}>
          <strong>Demo:</strong><br />
          📧 raj@exporters.in / password123<br />
          🛡️ admin@system.com / admin123
        </div>
      </div>
    </div>
  );
}

function Layout({ children }) {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const logout = () => {
    localStorage.clear();
    navigate('/');
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f1f5f9' }}>
      <nav style={{
        background: '#1e3a8a', color: 'white', padding: '12px 24px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Ship size={24} />
          <h2 style={{ margin: 0 }}>ShipTrack AI</h2>
        </div>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <Link to="/shipments" style={navLink}><Ship size={16} /> Shipments</Link>
          <Link to="/register" style={navLink}><Plus size={16} /> Register</Link>
          <Link to="/analytics" style={navLink}><BarChart3 size={16} /> Analytics</Link>
          <span style={{ fontSize: 14, opacity: 0.8 }}>{user.name}</span>
          <button onClick={logout} style={{
            background: '#dc2626', color: 'white', border: 'none',
            padding: '6px 12px', borderRadius: 6, cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: 4
          }}>
            <LogOut size={14} /> Logout
          </button>
        </div>
      </nav>
      <div style={{ padding: 24 }}>{children}</div>
    </div>
  );
}

const navLink = {
  color: 'white', textDecoration: 'none', display: 'flex',
  alignItems: 'center', gap: 4, fontSize: 14
};

function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/" />;
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/shipments" element={
          <ProtectedRoute><Layout><ShipmentList /></Layout></ProtectedRoute>
        } />
        <Route path="/register" element={
          <ProtectedRoute><Layout><RegisterShipment /></Layout></ProtectedRoute>
        } />
        <Route path="/analytics" element={
          <ProtectedRoute><Layout><Analytics /></Layout></ProtectedRoute>
        } />
        <Route path="/map/:id" element={
          <ProtectedRoute><Layout><ShipmentMap /></Layout></ProtectedRoute>
        } />
      </Routes>
    </Router>
  );
}

export default App;
