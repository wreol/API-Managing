import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import type { ApiKey, AlertEvent, KeyShare } from '../types';

export default function DashboardPage() {
  const navigate = useNavigate();
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);
  const [received, setReceived] = useState<KeyShare[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [keysRes, alertsRes, sharesRes] = await Promise.all([
          apiClient.get<ApiKey[]>('/keys'),
          apiClient.get<AlertEvent[]>('/alerts/events', { params: { unread_only: true } }),
          apiClient.get<KeyShare[]>('/team/shares', { params: { direction: 'received' } }),
        ]);
        setKeys(keysRes.data);
        setAlerts(alertsRes.data);
        setReceived(sharesRes.data);
      } catch {
        // Silently handle — dashboard shows empty states
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner"><div className="spinner" /></div>
      </div>
    );
  }

  const okKeys = keys.filter((k) => k.status === 'ok');
  const errorKeys = keys.filter((k) => k.status === 'error');
  const ownedKeys = keys.filter((k) => k.permission === null);

  return (
    <div className="page-container">
      <h2 className="section-title">Dashboard</h2>

      {/* Stat cards */}
      <div className="stat-grid">
        <div className="stat-card" onClick={() => navigate('/keys')} style={{ cursor: 'pointer' }}>
          <div className="stat-label">Your Keys</div>
          <div className="stat-value">{ownedKeys.length}</div>
        </div>
        <div className="stat-card" onClick={() => navigate('/alerts')} style={{ cursor: 'pointer' }}>
          <div className="stat-label">Key Health</div>
          <div className="stat-value">
            <span style={{ color: errorKeys.length > 0 ? 'var(--danger)' : 'var(--success)' }}>
              {errorKeys.length > 0 ? `${errorKeys.length} broken` : 'All OK'}
            </span>
          </div>
        </div>
        <div className="stat-card" onClick={() => navigate('/team')} style={{ cursor: 'pointer' }}>
          <div className="stat-label">Shared With You</div>
          <div className="stat-value">{received.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Unread Alerts</div>
          <div className="stat-value">{alerts.length}</div>
        </div>
      </div>

      {/* Quick actions */}
      <div className="flex-row gap-12 mb-24" style={{ marginTop: 24 }}>
        <button className="btn btn-primary" onClick={() => navigate('/keys')}>
          Manage Keys
        </button>
        <button className="btn btn-secondary" onClick={() => navigate('/alerts')}>
          View Alerts
        </button>
        <button className="btn btn-secondary" onClick={() => navigate('/team')}>
          Team Sharing
        </button>
      </div>

      {/* Key list preview — show error keys first */}
      {errorKeys.length > 0 && (
        <div className="card mb-24">
          <div className="card-header">
            <span className="card-title" style={{ color: 'var(--danger)' }}>
              Keys Needing Attention
            </span>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Label</th>
                  <th>Provider</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {errorKeys.map((k) => (
                  <tr key={k.id} className="clickable" onClick={() => navigate(`/keys/${k.id}`)}>
                    <td>{k.label}</td>
                    <td>{k.provider}</td>
                    <td><span className="badge badge-danger">Error</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* All keys overview */}
      {keys.length > 0 && (
        <div className="card mb-24">
          <div className="card-header">
            <span className="card-title">All Keys</span>
            <span style={{ color: 'var(--text-secondary)', fontSize: 12 }}>
              {okKeys.length}/{keys.length} healthy
            </span>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Label</th>
                  <th>Provider</th>
                  <th>Access</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {keys.map((k) => (
                  <tr key={k.id} className="clickable" onClick={() => navigate(`/keys/${k.id}`)}>
                    <td>{k.label}</td>
                    <td>{k.provider}</td>
                    <td>
                      <span className="badge badge-default" style={{ fontSize: 10 }}>
                        {k.permission === null ? 'Owner' : k.permission}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${k.status === 'ok' ? 'badge-success' : 'badge-danger'}`}>
                        {k.status === 'ok' ? 'OK' : 'Error'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty state */}
      {keys.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon">+</div>
          <div className="empty-state-title">Welcome to API Vault</div>
          <div className="empty-state-desc">
            Add your first API key to start monitoring, sharing, and getting alerts.
          </div>
          <button className="btn btn-primary" onClick={() => navigate('/keys')}>
            Add Your First Key
          </button>
        </div>
      )}

      {/* Recent alerts */}
      {alerts.length > 0 && (
        <div className="card mt-24">
          <div className="card-header">
            <span className="card-title">Recent Alerts ({alerts.length} unread)</span>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/alerts')}>
              View All
            </button>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Message</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {alerts.slice(0, 5).map((a) => (
                  <tr key={a.id}>
                    <td style={{ fontSize: 13 }}>{a.message}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: 11, whiteSpace: 'nowrap' }}>
                      {new Date(a.triggered_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
