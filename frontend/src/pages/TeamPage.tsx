import { useState, useEffect, useCallback } from 'react';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import type { KeyShare, ApiKey } from '../types';

export default function TeamPage() {
  const { user } = useAuth();
  const [shares, setShares] = useState<KeyShare[]>([]);
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);

  // Form state
  const [formEmail, setFormEmail] = useState('');
  const [formKeyId, setFormKeyId] = useState('');
  const [formPermission, setFormPermission] = useState('read');
  const [formError, setFormError] = useState('');
  const [formLoading, setFormLoading] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [sentRes, receivedRes, keysRes] = await Promise.all([
        apiClient.get<KeyShare[]>('/team/shares', { params: { direction: 'sent' } }),
        apiClient.get<KeyShare[]>('/team/shares', { params: { direction: 'received' } }),
        apiClient.get<ApiKey[]>('/keys'),
      ]);
      setShares([...sentRes.data, ...receivedRes.data]);
      setKeys(keysRes.data);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? 'Failed to load team data.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  async function handleShare(e: React.FormEvent) {
    e.preventDefault();
    setFormError('');
    setFormLoading(true);
    try {
      await apiClient.post('/team/share', {
        key_id: formKeyId,
        shared_with_email: formEmail,
        permission: formPermission,
      });
      setShowModal(false);
      setFormEmail('');
      setFormKeyId('');
      setFormPermission('read');
      fetchData();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFormError(detail ?? 'Failed to share key.');
    } finally {
      setFormLoading(false);
    }
  }

  async function handleRevoke(shareId: string) {
    if (!confirm('Revoke this share? The user will lose access.')) return;
    try {
      await apiClient.delete(`/team/share/${shareId}`);
      fetchData();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(detail ?? 'Failed to revoke share.');
    }
  }

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner"><div className="spinner" /></div>
      </div>
    );
  }

  const sentShares = shares.filter((s) => s.shared_by_email === user?.email);
  const receivedShares = shares.filter((s) => s.shared_with_email === user?.email);

  return (
    <div className="page-container">
      {error && <div className="alert alert-error">{error}</div>}

      <div className="section-header">
        <h2 className="section-title">Team Sharing</h2>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          Share Key
        </button>
      </div>

      {/* Sent Shares */}
      <div className="section-header mt-16">
        <h3 className="section-title" style={{ fontSize: 14 }}>Sent Shares</h3>
      </div>
      {sentShares.length === 0 ? (
        <div className="card mb-24">
          <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-secondary)' }}>
            You haven't shared any keys yet.
          </div>
        </div>
      ) : (
        <div className="card mb-24">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Key</th>
                  <th>Shared With</th>
                  <th>Permission</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sentShares.map((s) => (
                  <tr key={s.id}>
                    <td>
                      <div>{s.key_label}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{s.masked_key}</div>
                    </td>
                    <td>{s.shared_with_email}</td>
                    <td>
                      <span className={`badge ${s.permission === 'use' ? 'badge-accent' : 'badge-default'}`}>
                        {s.permission}
                      </span>
                    </td>
                    <td>
                      <button className="btn btn-danger btn-sm" onClick={() => handleRevoke(s.id)}>
                        Revoke
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Received Shares */}
      <div className="section-header mt-16">
        <h3 className="section-title" style={{ fontSize: 14 }}>Received Shares</h3>
      </div>
      {receivedShares.length === 0 ? (
        <div className="card">
          <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-secondary)' }}>
            No keys have been shared with you yet.
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Key</th>
                  <th>Shared By</th>
                  <th>Permission</th>
                </tr>
              </thead>
              <tbody>
                {receivedShares.map((s) => (
                  <tr key={s.id}>
                    <td>
                      <div>{s.key_label}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{s.masked_key}</div>
                    </td>
                    <td>{s.shared_by_email}</td>
                    <td>
                      <span className={`badge ${s.permission === 'use' ? 'badge-accent' : 'badge-default'}`}>
                        {s.permission}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Share Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Share API Key</h2>
            {formError && <div className="alert alert-error">{formError}</div>}
            <form onSubmit={handleShare}>
              <div className="form-group">
                <label className="form-label">User Email</label>
                <input
                  className="form-input"
                  type="email"
                  value={formEmail}
                  onChange={(e) => setFormEmail(e.target.value)}
                  placeholder="colleague@example.com"
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">API Key</label>
                <select
                  className="form-select"
                  value={formKeyId}
                  onChange={(e) => setFormKeyId(e.target.value)}
                  required
                >
                  <option value="">Select a key...</option>
                  {keys.map((k) => (
                    <option key={k.id} value={k.id}>{k.label} ({k.provider})</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Permission</label>
                <select
                  className="form-select"
                  value={formPermission}
                  onChange={(e) => setFormPermission(e.target.value)}
                >
                  <option value="read">Read (view key info)</option>
                  <option value="use">Use (make API calls)</option>
                </select>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={formLoading}>
                  {formLoading ? 'Sharing...' : 'Share'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
