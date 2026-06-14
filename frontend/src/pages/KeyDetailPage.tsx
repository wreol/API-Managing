import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import type { KeyDetail } from '../types';

export default function KeyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [keyDetail, setKeyDetail] = useState<KeyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ status: string; message: string } | null>(null);

  const fetchData = useCallback(async () => {
    if (!id) return;
    try {
      const keyRes = await apiClient.get<KeyDetail>(`/keys/${id}`);
      setKeyDetail(keyRes.data);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? 'Failed to load key details.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { fetchData(); }, [fetchData]);

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

  async function handleTestConnection() {
    if (!id) return;
    setTesting(true);
    setTestResult(null);
    try {
      const { data } = await apiClient.post<{ status: string; message: string; provider: string }>(`/keys/${id}/test`);
      setTestResult(data);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setTestResult({ status: 'error', message: detail ?? 'Test failed' });
    } finally {
      setTesting(false);
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
        <button className="btn btn-secondary mt-16" onClick={() => navigate('/keys')}>Back to Keys</button>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="section-header">
        <div className="flex-row gap-8">
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/keys')}>&larr; Back</button>
          <h2 className="section-title">{keyDetail.label}</h2>
        </div>
        <div className="flex-row gap-8">
          <button className="btn btn-secondary btn-sm" onClick={handleTestConnection} disabled={testing}>
            {testing ? 'Testing...' : 'Test Connection'}
          </button>
          <button className="btn btn-primary btn-sm" onClick={handleCopy}>
            {copied ? 'Copied!' : 'Copy Key'}
          </button>
        </div>
      </div>

      {/* Test result banner */}
      {testResult && (
        <div className={`alert ${testResult.status === 'ok' ? 'alert-success' : 'alert-error'} mb-16`}>
          {testResult.status === 'ok' ? '✓ ' : '✗ '}{testResult.message}
        </div>
      )}

      <div className="card">
        <div className="detail-grid">
          <div className="detail-label">Provider</div>
          <div className="detail-value">{keyDetail.provider}</div>

          <div className="detail-label">Label</div>
          <div className="detail-value">{keyDetail.label}</div>

          <div className="detail-label">Masked Key</div>
          <div className="detail-value"><span className="masked-key">{keyDetail.masked_key}</span></div>

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
    </div>
  );
}
