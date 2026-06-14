import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import type { KeyDetail, KeyBreakdown } from '../types';

export default function KeyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [keyDetail, setKeyDetail] = useState<KeyDetail | null>(null);
  const [usage, setUsage] = useState<KeyBreakdown | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const fetchData = useCallback(async () => {
    if (!id) return;
    try {
      const [keyRes, keysRes] = await Promise.all([
        apiClient.get<KeyDetail>(`/keys/${id}`),
        apiClient.get<KeyBreakdown[]>('/usage/by-key'),
      ]);
      setKeyDetail(keyRes.data);
      const keyUsage = keysRes.data.find((k: KeyBreakdown) => k.key_id === id);
      setUsage(keyUsage ?? null);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? 'Failed to load key details.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  async function handleCopy() {
    if (!id) return;
    try {
      const { data } = await apiClient.post<{ key_value: string }>(`/keys/${id}/copy`);
      await navigator.clipboard.writeText(data.key_value);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(detail ?? 'Failed to copy key.');
    }
  }

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner"><div className="spinner" /></div>
      </div>
    );
  }

  if (error || !keyDetail) {
    return (
      <div className="page-container">
        <div className="alert alert-error">{error ?? 'Key not found.'}</div>
        <button className="btn btn-secondary mt-16" onClick={() => navigate('/keys')}>
          Back to Keys
        </button>
      </div>
    );
  }

  function formatCost(n: number): string {
    return `$${n.toFixed(4)}`;
  }

  return (
    <div className="page-container">
      <div className="section-header">
        <div className="flex-row gap-8">
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/keys')}>
            &larr; Back
          </button>
          <h2 className="section-title">{keyDetail.label}</h2>
        </div>
        <div className="flex-row gap-8">
          <button className="btn btn-secondary btn-sm" onClick={handleCopy}>
            {copied ? 'Copied!' : 'Copy Key'}
          </button>
        </div>
      </div>

      <div className="card mb-24">
        <div className="detail-grid">
          <div className="detail-label">Provider</div>
          <div className="detail-value">{keyDetail.provider}</div>

          <div className="detail-label">Label</div>
          <div className="detail-value">{keyDetail.label}</div>

          <div className="detail-label">Masked Key</div>
          <div className="detail-value">
            <span className="masked-key">{keyDetail.masked_key}</span>
          </div>

          <div className="detail-label">Status</div>
          <div className="detail-value">
            <span className={`badge ${keyDetail.status === 'ok' ? 'badge-success' : keyDetail.status === 'error' ? 'badge-danger' : 'badge-warning'}`}>
              {keyDetail.status}
            </span>
          </div>

          <div className="detail-label">Active</div>
          <div className="detail-value">
            <span className={`badge ${keyDetail.is_active ? 'badge-success' : 'badge-danger'}`}>
              {keyDetail.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>

          {keyDetail.tags && keyDetail.tags.length > 0 && (
            <>
              <div className="detail-label">Tags</div>
              <div className="detail-value flex-row flex-wrap gap-8">
                {keyDetail.tags.map((tag) => (
                  <span key={tag} className="badge badge-default">{tag}</span>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {usage ? (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Usage Summary</span>
          </div>
          <div className="detail-grid">
            <div className="detail-label">Calls</div>
            <div className="detail-value">{usage.calls.toLocaleString()}</div>
            <div className="detail-label">Tokens</div>
            <div className="detail-value">{usage.tokens.toLocaleString()}</div>
            <div className="detail-label">Cost</div>
            <div className="detail-value" style={{ fontFamily: 'var(--font-mono)' }}>
              {formatCost(usage.cost)}
            </div>
          </div>
        </div>
      ) : (
        <div className="card">
          <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-secondary)' }}>
            No usage data for this key yet.
          </div>
        </div>
      )}
    </div>
  );
}
