import { useState, useEffect, useCallback } from 'react';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import type { AlertRule, AlertEvent, ApiKey } from '../types';

export default function AlertsPage() {
  const { user } = useAuth();
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [events, setEvents] = useState<AlertEvent[]>([]);
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);

  const [formKeyId, setFormKeyId] = useState('');
  const [formNotifyEmail, setFormNotifyEmail] = useState(user?.email ?? '');
  const [formError, setFormError] = useState('');
  const [formLoading, setFormLoading] = useState(false);

  // Map key_id -> label for display
  const keyLabel = useCallback(
    (keyId: string) => keys.find((k) => k.id === keyId)?.label ?? keyId.slice(0, 8) + '...',
    [keys],
  );

  const fetchData = useCallback(async () => {
    try {
      const [rulesRes, eventsRes, keysRes] = await Promise.all([
        apiClient.get<AlertRule[]>('/alerts/rules'),
        apiClient.get<AlertEvent[]>('/alerts/events'),
        apiClient.get<ApiKey[]>('/keys'),
      ]);
      setRules(rulesRes.data);
      setEvents(eventsRes.data);
      setKeys(keysRes.data);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? 'Failed to load alerts.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  async function handleCreateRule(e: React.FormEvent) {
    e.preventDefault();
    setFormError('');
    setFormLoading(true);
    try {
      await apiClient.post('/alerts/rules', {
        key_id: formKeyId,
        notify_email: formNotifyEmail,
      });
      setShowModal(false);
      setFormKeyId('');
      fetchData();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFormError(detail ?? 'Failed to create alert rule.');
    } finally {
      setFormLoading(false);
    }
  }

  async function handleDeleteRule(ruleId: string) {
    if (!confirm('Delete this alert rule?')) return;
    try {
      await apiClient.delete(`/alerts/rules/${ruleId}`);
      fetchData();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(detail ?? 'Failed to delete rule.');
    }
  }

  async function handleToggleRule(rule: AlertRule) {
    try {
      await apiClient.patch(`/alerts/rules/${rule.id}`, { is_active: !rule.is_active });
      fetchData();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(detail ?? 'Failed to update rule.');
    }
  }

  async function handleMarkRead(eventId: string) {
    try {
      await apiClient.patch(`/alerts/events/${eventId}/read`);
      fetchData();
    } catch { /* ignore */ }
  }

  const emailNotVerified = !!(user && !user.email_verified);

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner"><div className="spinner" /></div>
      </div>
    );
  }

  return (
    <div className="page-container">
      {error && <div className="alert alert-error">{error}</div>}

      {/* Alert Rules */}
      <div className="section-header">
        <h2 className="section-title">Alert Rules</h2>
        <button
          className="btn btn-primary"
          onClick={() => setShowModal(true)}
          disabled={emailNotVerified}
          title={emailNotVerified ? 'Verify your email to create alerts' : undefined}
        >
          Create Rule
        </button>
      </div>

      {emailNotVerified && (
        <div className="alert alert-info mb-16">
          You need a verified email address to create alert rules.
        </div>
      )}

      {rules.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">!</div>
          <div className="empty-state-title">No Alert Rules</div>
          <div className="empty-state-desc">
            Create alert rules to get notified when a key stops working.
          </div>
          {!emailNotVerified && (
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>
              Create Your First Alert
            </button>
          )}
        </div>
      ) : (
        <div className="card mb-24">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Key</th>
                  <th>Notify</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((rule) => (
                  <tr key={rule.id}>
                    <td>{keyLabel(rule.key_id)}</td>
                    <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{rule.notify_email}</td>
                    <td>
                      <span className={`badge ${rule.is_active ? 'badge-success' : 'badge-default'}`}>
                        {rule.is_active ? 'Active' : 'Paused'}
                      </span>
                    </td>
                    <td>
                      <div className="row-actions">
                        <button className="btn btn-ghost btn-sm" onClick={() => handleToggleRule(rule)}>
                          {rule.is_active ? 'Pause' : 'Resume'}
                        </button>
                        <button className="btn btn-danger btn-sm" onClick={() => handleDeleteRule(rule.id)}>
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Alert Events */}
      <div className="section-header mt-24">
        <h2 className="section-title">Recent Alert Events</h2>
      </div>

      {events.length === 0 ? (
        <div className="card">
          <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-secondary)' }}>
            No alert events triggered yet.
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Message</th>
                  <th>Triggered</th>
                  <th>Email</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {events.map((evt) => (
                  <tr key={evt.id}>
                    <td style={{ maxWidth: 300 }}>{evt.message}</td>
                    <td style={{ fontSize: 12, whiteSpace: 'nowrap' }}>
                      {new Date(evt.triggered_at).toLocaleString()}
                    </td>
                    <td><span className={`badge ${evt.email_sent ? 'badge-success' : 'badge-default'}`}>{evt.email_sent ? 'Sent' : 'No'}</span></td>
                    <td><span className={`badge ${evt.is_read ? 'badge-default' : 'badge-warning'}`}>{evt.is_read ? 'Read' : 'Unread'}</span></td>
                    <td>
                      {!evt.is_read && (
                        <button className="btn btn-ghost btn-sm" onClick={() => handleMarkRead(evt.id)}>Mark Read</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create Rule Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Create Key Health Alert</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginBottom: 16 }}>
              Get notified when this API key stops working.
            </p>
            {formError && <div className="alert alert-error">{formError}</div>}
            <form onSubmit={handleCreateRule}>
              <div className="form-group">
                <label className="form-label">API Key</label>
                <select className="form-select" value={formKeyId} onChange={(e) => setFormKeyId(e.target.value)} required>
                  <option value="">Select a key...</option>
                  {keys.map((k) => (
                    <option key={k.id} value={k.id}>{k.label} ({k.provider})</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Notification Email</label>
                <input className="form-input" type="email" value={formNotifyEmail} onChange={(e) => setFormNotifyEmail(e.target.value)} required />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={formLoading}>
                  {formLoading ? 'Creating...' : 'Create Rule'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
