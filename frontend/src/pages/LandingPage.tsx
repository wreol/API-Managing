import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const features = [
  {
    icon: 'K',
    title: 'Key Vault',
    description: 'Securely store and manage all your API keys in one encrypted vault.',
  },
  {
    icon: '#',
    title: 'Usage Dashboard',
    description: 'Real-time dashboards for calls, tokens, and costs across every provider.',
  },
  {
    icon: '!',
    title: 'Budget Alerts',
    description: 'Set thresholds and get notified before you exceed your budget limits.',
  },
  {
    icon: '@',
    title: 'Team Sharing',
    description: 'Share API keys with your team without exposing the raw key values.',
  },
];

export default function LandingPage() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="loading-spinner">
        <div className="spinner" />
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="landing-page">
      <header className="landing-header">
        <div className="landing-logo">API Vault</div>
        <div className="landing-header-actions">
          <Link to="/login" className="btn btn-secondary">
            Log in
          </Link>
          <Link to="/register" className="btn btn-primary">
            Get Started
          </Link>
        </div>
      </header>

      <section className="landing-hero">
        <h1>Manage All Your AI APIs in One Place</h1>
        <p>
          Track usage, control costs, and share keys securely across OpenAI,
          Anthropic, DeepSeek, and custom providers. Built for developers who
          want visibility without vendor lock-in.
        </p>
        <Link to="/register" className="btn btn-primary btn-lg">
          Get Started
        </Link>
      </section>

      <section className="landing-features">
        {features.map((f) => (
          <div key={f.title} className="feature-card">
            <div className="feature-card-icon">{f.icon}</div>
            <h3>{f.title}</h3>
            <p>{f.description}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
