import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import type { ApiKey, ProviderInfo } from '../types';

type WizardStep = 1 | 2 | 3;

export default function OnboardingPage() {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState<WizardStep>(1);
  const [isVerified, setIsVerified] = useState(user?.email_verified ?? false);

  // Step 2 form
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [formProvider, setFormProvider] = useState('');
  const [formLabel, setFormLabel] = useState('');
  const [formKeyValue, setFormKeyValue] = useState('');
  const [formError, setFormError] = useState('');
  const [formLoading, setFormLoading] = useState(false);
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [checkingVerified, setCheckingVerified] = useState(false);

  useEffect(() => {
    async function fetchProviders() {
      try {
        const { data } = await apiClient.get<ProviderInfo[]>('/providers');
        setProviders(data);
      } catch {
        // ignore
      }
    }
    async function fetchKeys() {
      try {
        const { data } = await apiClient.get<ApiKey[]>('/keys');
        setKeys(data);
      } catch {
        // ignore
      }
    }
    if (step >= 2) {
      fetchProviders();
      fetchKeys();
    }
  }, [step]);

  async function handleCheckVerification() {
    setCheckingVerified(true);
    try {
      await refreshUser();
      setIsVerified(user?.email_verified ?? false);
    } catch {
      // ignore
    } finally {
      setCheckingVerified(false);
    }
  }

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
      setKeys((prev) => [...prev, { id: 'temp', provider: formProvider, label: formLabel, masked_key: '', tags: [], status: 'ok', is_active: true, permission: null } as ApiKey]);
      setStep(3);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFormError(detail ?? 'Failed to add key.');
    } finally {
      setFormLoading(false);
    }
  }

  return (
    <div className="page-container">
      {/* Wizard Steps */}
      <div className="wizard-steps">
        <div className={`wizard-step ${step === 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
          <span className="wizard-step-number">{step > 1 ? 'x' : '1'}</span>
          Verify Email
        </div>
        <div className={`wizard-step ${step === 2 ? 'active' : ''} ${step > 2 ? 'completed' : ''}`}>
          <span className="wizard-step-number">{step > 2 ? 'x' : '2'}</span>
          Add First Key
        </div>
        <div className={`wizard-step ${step === 3 ? 'active' : ''}`}>
          <span className="wizard-step-number">3</span>
          Done
        </div>
      </div>

      {/* Step 1: Verify Email */}
      {step === 1 && (
        <div className="wizard-content">
          <h2>Verify Your Email</h2>
          <p>
            A verified email is required to create alert rules and receive notifications.
            {isVerified
              ? ' Your email is already verified.'
              : ' A verification link was sent to your email.'}
          </p>
          {isVerified ? (
            <button className="btn btn-primary btn-lg" onClick={() => setStep(2)}>
              Continue
            </button>
          ) : (
            <div className="flex-row gap-8" style={{ justifyContent: 'center' }}>
              <button
                className="btn btn-primary"
                onClick={handleCheckVerification}
                disabled={checkingVerified}
              >
                {checkingVerified ? 'Checking...' : 'I have verified'}
              </button>
              <button className="btn btn-ghost" onClick={() => setStep(2)}>
                Skip for now
              </button>
            </div>
          )}
        </div>
      )}

      {/* Step 2: Add First Key */}
      {step === 2 && (
        <div className="wizard-content">
          <h2>Add Your First API Key</h2>
          <p>
            Add an API key from one of your providers to start tracking usage.
            Your key is encrypted at rest.
          </p>
          {keys.length > 0 && (
            <div className="card mb-16" style={{ textAlign: 'left' }}>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 8 }}>
                Existing keys:
              </div>
              {keys.map((k) => (
                <div key={k.id} className="flex-between mb-8" style={{ fontSize: 13 }}>
                  <span>{k.label}</span>
                  <span className="badge badge-default">{k.provider}</span>
                </div>
              ))}
            </div>
          )}
          {formError && <div className="alert alert-error">{formError}</div>}
          <form onSubmit={handleAddKey} style={{ textAlign: 'left' }}>
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
                placeholder="e.g. My OpenAI Key"
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
            <div className="flex-row gap-8" style={{ justifyContent: 'center' }}>
              <button type="submit" className="btn btn-primary" disabled={formLoading}>
                {formLoading ? 'Adding...' : 'Add Key'}
              </button>
              <button type="button" className="btn btn-ghost" onClick={() => setStep(3)}>
                Skip
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Step 3: Done */}
      {step === 3 && (
        <div className="wizard-content">
          <h2>You are all set!</h2>
          <p>
            Your API keys are secure and we are ready to track your usage.
            Head to the dashboard to see your data.
          </p>
          <button className="btn btn-primary btn-lg" onClick={() => navigate('/dashboard')}>
            Go to Dashboard
          </button>
        </div>
      )}
    </div>
  );
}
