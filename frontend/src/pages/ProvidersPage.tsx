import { useState, useEffect, useCallback } from 'react';
import apiClient from '../api/client';
import type { ProviderInfo } from '../types';

export default function ProvidersPage() {
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);

  // Form state
  const [formName, setFormName] = useState('');
  const [formLabel, setFormLabel] = useState('');
  const [formBaseUrl, setFormBaseUrl] = useState('');
  const [formAuthType, setFormAuthType] = useState('bearer');
  const [formAuthHeader, setFormAuthHeader] = useState('X-API-Key');
  const [formError, setFormError] = useState('');
  const [formLoading, setFormLoading] = useState(false);

  const fetchProviders = useCallback(async () => {
    try {
      const { data } = await apiClient.get<ProviderInfo[]>('/providers');
      setProviders(data);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? 'Failed to load providers.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProviders();
  }, [fetchProviders]);

  async function handleAddProvider(e: React.FormEvent) {
    e.preventDefault();
    setFormError('');
    setFormLoading(true);
    try {
      await apiClient.post('/providers/custom', {
        name: formName,
        label: formLabel,
        base_url: formBaseUrl,
        auth_type: formAuthType,
        auth_header_name: formAuthHeader,
      });
      setShowModal(false);
      setFormName('');
      setFormLabel('');
      setFormBaseUrl('');
      setFormAuthType('bearer');
      setFormAuthHeader('X-API-Key');
      fetchProviders();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFormError(detail ?? 'Failed to add provider.');
    } finally {
      setFormLoading(false);
    }
  }

  async function handleDelete(providerName: string) {
    if (!confirm(`Remove provider "${providerName}"? This will not delete existing keys.`)) return;
    try {
      await apiClient.delete(`/providers/custom/${providerName}`);
      fetchProviders();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(detail ?? 'Failed to remove provider.');
    }
  }

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner"><div className="spinner" /></div>
      </div>
    );
  }

  const builtIn = providers.filter((p) => !p.is_custom);
  const custom = providers.filter((p) => p.is_custom);

  return (
    <div className="page-container">
      {error && <div className="alert alert-error">{error}</div>}

      <div className="section-header">
        <h2 className="section-title">Providers</h2>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          Add Custom
        </button>
      </div>

      {/* Built-in Providers */}
      <div className="section-header mt-16">
        <h3 className="section-title" style={{ fontSize: 14 }}>Built-in</h3>
      </div>
      {builtIn.length === 0 ? (
        <div className="card mb-24">
          <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-secondary)' }}>
            No built-in providers registered.
          </div>
        </div>
      ) : (
        <div className="card mb-24">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Label</th>
                  <th>Type</th>
                </tr>
              </thead>
              <tbody>
                {builtIn.map((p) => (
                  <tr key={p.name}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>{p.name}</td>
                    <td>{p.label}</td>
                    <td><span className="badge badge-accent">Built-in</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Custom Providers */}
      <div className="section-header mt-16">
        <h3 className="section-title" style={{ fontSize: 14 }}>Custom</h3>
      </div>
      {custom.length === 0 ? (
        <div className="card">
          <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-secondary)' }}>
            No custom providers yet. Add one to support additional API services.
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Label</th>
                  <th>Type</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {custom.map((p) => (
                  <tr key={p.name}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>{p.name}</td>
                    <td>{p.label}</td>
                    <td><span className="badge badge-warning">Custom</span></td>
                    <td>
                      <button className="btn btn-danger btn-sm" onClick={() => handleDelete(p.name)}>
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add Custom Provider Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Add Custom Provider</h2>
            {formError && <div className="alert alert-error">{formError}</div>}
            <form onSubmit={handleAddProvider}>
              <div className="form-group">
                <label className="form-label">Name (slug)</label>
                <input
                  className="form-input"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="e.g. my-custom-llm"
                  required
                  pattern="[a-z0-9_-]+"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Display Label</label>
                <input
                  className="form-input"
                  value={formLabel}
                  onChange={(e) => setFormLabel(e.target.value)}
                  placeholder="e.g. My Custom LLM"
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Base URL</label>
                <input
                  className="form-input"
                  type="url"
                  value={formBaseUrl}
                  onChange={(e) => setFormBaseUrl(e.target.value)}
                  placeholder="https://api.example.com"
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Auth Type</label>
                <select className="form-select" value={formAuthType} onChange={(e) => setFormAuthType(e.target.value)}>
                  <option value="bearer">Bearer Token</option>
                  <option value="custom_header">Custom Header</option>
                </select>
              </div>
              {formAuthType === 'custom_header' && (
                <div className="form-group">
                  <label className="form-label">Auth Header Name</label>
                  <input
                    className="form-input"
                    value={formAuthHeader}
                    onChange={(e) => setFormAuthHeader(e.target.value)}
                    placeholder="X-API-Key"
                  />
                </div>
              )}
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={formLoading}>
                  {formLoading ? 'Adding...' : 'Add Provider'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
