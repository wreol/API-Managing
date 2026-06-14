import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import type { ApiKey, ProviderInfo } from '../types';

export default function KeysPage() {
  const navigate = useNavigate();
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [formProvider, setFormProvider] = useState('');
  const [formLabel, setFormLabel] = useState('');
  const [formKeyValue, setFormKeyValue] = useState('');
  const [formError, setFormError] = useState('');
  const [formLoading, setFormLoading] = useState(false);

  const fetchKeys = useCallback(async () => {
    try {
      const [keysRes, providersRes] = await Promise.all([
        apiClient.get<ApiKey[]>('/keys'),
        apiClient.get<ProviderInfo[]>('/providers'),
      ]);
      setKeys(keysRes.data);
      setProviders(providersRes.data);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? 'Failed to load keys.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchKeys();
  }, [fetchKeys]);

  async function handleAddKey(e: React.FormEvent) {
    e.preventDefault();
    setFormError('');
    setFormLoading(true);
    try {
      await apiClient.post('/keys', {
        provider: formProvider,
        label: formLabel,
        key_value: formKeyValue,
      });
      setShowModal(false);
      setFormProvider('');
      setFormLabel('');
      setFormKeyValue('');
      fetchKeys();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFormError(detail ?? 'Failed to add key.');
    } finally {
      setFormLoading(false);
    }
  }

  async function handleDelete(keyId: string) {
    if (!confirm('Are you sure you want to delete this key? This cannot be undone.')) return;
    try {
      await apiClient.delete(`/keys/${keyId}`);
      fetchKeys();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(detail ?? 'Failed to delete key.');
    }
  }

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

      <div className="section-header">
        <h2 className="section-title">API Keys</h2>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          Add Key
        </button>
      </div>

      {keys.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">*</div>
          <div className="empty-state-title">No API Keys</div>
          <div className="empty-state-desc">
            Add your first API key to start tracking usage and managing access.
          </div>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            Add Your First Key
          </button>
        </div>
      ) : (
        <div className="card">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Label</th>
                  <th>Provider</th>
                  <th>Key</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {keys.map((key) => (
                  <tr key={key.id}>
                    <td>
                      <span
                        style={{ cursor: 'pointer', fontWeight: 500 }}
                        onClick={() => navigate(`/keys/${key.id}`)}
                      >
                        {key.label}
                      </span>
                    </td>
                    <td>{key.provider}</td>
                    <td><span className="masked-key">{key.masked_key}</span></td>
                    <td>
                      <span className={`badge ${key.status === 'ok' ? 'badge-success' : key.status === 'error' ? 'badge-danger' : 'badge-warning'}`}>
                        {key.status}
                      </span>
                    </td>
                    <td>
                      <div className="row-actions">
                        <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/keys/${key.id}`)}>
                          Details
                        </button>
                        <button className="btn btn-danger btn-sm" onClick={() => handleDelete(key.id)}>
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

      {/* Add Key Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Add API Key</h2>
            {formError && <div className="alert alert-error">{formError}</div>}
            <form onSubmit={handleAddKey}>
              <div className="form-group">
                <label className="form-label">Provider</label>
                <select
                  className="form-select"
                  value={formProvider}
                  onChange={(e) => setFormProvider(e.target.value)}
                  required
                >
                  <option value="">Select a provider...</option>
                  {providers.map((p) => (
                    <option key={p.name} value={p.name}>{p.label}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Label</label>
                <input
                  className="form-input"
                  value={formLabel}
                  onChange={(e) => setFormLabel(e.target.value)}
                  placeholder="e.g. Production OpenAI Key"
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">API Key Value</label>
                <input
                  className="form-input"
                  type="password"
                  value={formKeyValue}
                  onChange={(e) => setFormKeyValue(e.target.value)}
                  placeholder="sk-..."
                  required
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={formLoading}>
                  {formLoading ? 'Adding...' : 'Add Key'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
