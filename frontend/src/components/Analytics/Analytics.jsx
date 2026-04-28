import React, { useState, useEffect } from 'react';
import { analyticsAPI, shipmentAPI } from '../../services/api';
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Zap } from 'lucide-react';

export default function Analytics() {
  const [dashboard, setDashboard] = useState(null);
  const [insights, setInsights] = useState('');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [aiLoading, setAiLoading] = useState(false);
  const [err, setErr] = useState('');

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const response = await analyticsAPI.getDashboard(30);
      setDashboard(response.data);
      setErr('');
    } catch (e) {
      setErr('Failed to load analytics');
      console.error('Analytics error:', e);
    } finally {
      setLoading(false);
    }
  };

  const getAIInsights = async () => {
    if (!query.trim()) return;
    setAiLoading(true);
    try {
      const { data } = await analyticsAPI.getAIInsights(query);
      const response = data.response || data.insights;
      setInsights(typeof response === 'string' ? response : JSON.stringify(response));
    } catch (e) {
      setInsights('Unable to get AI insights at this moment.');
    } finally {
      setAiLoading(false);
    }
  };

  const StatCard = ({ icon: Icon, label, value, trend, color }) => (
    <div style={{
      background: 'white', padding: 20, borderRadius: 12,
      borderLeft: `4px solid ${color}`
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={{ fontSize: 32 }}><Icon size={32} /></div>
        {trend && <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: trend > 0 ? '#10b981' : '#ef4444' }}>
          {trend > 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
          <span style={{ fontSize: 12 }}>{Math.abs(trend)}%</span>
        </div>}
      </div>
      <div style={{ fontSize: 12, color: '#64748b', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 'bold', color: '#1e3a8a' }}>{value}</div>
    </div>
  );

  return (
    <div>
      <h1>📊 Analytics Dashboard</h1>

      {err && <div style={{ padding: 12, background: '#fee2e2', color: '#991b1b', borderRadius: 8, marginBottom: 16 }}>{err}</div>}

      {loading ? (
        <p>Loading analytics...</p>
      ) : dashboard ? (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 16, marginBottom: 24 }}>
            <StatCard
              icon={CheckCircle} label="On-Time Rate" value={`${dashboard.on_time_rate}%`}
              trend={dashboard.on_time_rate > 85 ? 5 : -3} color="#10b981"
            />
            <StatCard
              icon={AlertTriangle} label="Delayed Shipments"
              value={dashboard.total_delays} trend={-10} color="#ef4444"
            />
            <StatCard
              icon={TrendingUp} label="Avg Delay"
              value={`${dashboard.avg_delay_hours}h`} color="#f59e0b"
            />
            <StatCard
              icon={Zap} label="Routes Optimized"
              value={dashboard.total_optimizations} color="#8b5cf6"
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
            <div style={{ background: 'white', padding: 20, borderRadius: 12 }}>
              <h3 style={{ marginTop: 0, marginBottom: 12 }}>Cargo Distribution</h3>
              {dashboard.cargo_distribution && Object.entries(dashboard.cargo_distribution).map(([cargo, count]) => (
                <div key={cargo} style={{ marginBottom: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: 12 }}>{cargo}</span>
                    <span style={{ fontWeight: 'bold' }}>{count}</span>
                  </div>
                  <div style={{ height: 8, background: '#e2e8f0', borderRadius: 4, overflow: 'hidden' }}>
                    <div style={{
                      height: '100%', background: '#8b5cf6',
                      width: `${(count / (dashboard.total_shipments || 1)) * 100}%`
                    }} />
                  </div>
                </div>
              ))}
            </div>

            <div style={{ background: 'white', padding: 20, borderRadius: 12 }}>
              <h3 style={{ marginTop: 0, marginBottom: 12 }}>Status Summary</h3>
              {dashboard.status_distribution && Object.entries(dashboard.status_distribution).map(([status, count]) => (
                <div key={status} style={{
                  padding: 8, background: '#f1f5f9', borderRadius: 6,
                  marginBottom: 8, display: 'flex', justifyContent: 'space-between'
                }}>
                  <span style={{ textTransform: 'uppercase', fontSize: 12 }}>{status}</span>
                  <span style={{ fontWeight: 'bold' }}>{count}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ background: 'white', padding: 20, borderRadius: 12 }}>
            <h3 style={{ marginTop: 0, marginBottom: 12 }}>🤖 AI Insights</h3>
            <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
              <input
                type="text" value={query} onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask about your shipments... (e.g., 'Why are delays increasing?')"
                style={{
                  flex: 1, padding: 10, borderRadius: 6, border: '1px solid #cbd5e1'
                }}
                onKeyPress={(e) => e.key === 'Enter' && getAIInsights()}
              />
              <button onClick={getAIInsights} disabled={aiLoading}
                style={{
                  padding: '10px 20px', background: '#1e3a8a', color: 'white',
                  border: 'none', borderRadius: 6, cursor: 'pointer'
                }}
              >
                {aiLoading ? '⏳' : '🔍'}
              </button>
            </div>
            {insights && (
              <div style={{
                padding: 12, background: '#f0f4ff', borderRadius: 6,
                borderLeft: '4px solid #8b5cf6', fontSize: 14, lineHeight: 1.6
              }}>
                {insights}
              </div>
            )}
          </div>
        </>
      ) : null}
    </div>
  );
}
