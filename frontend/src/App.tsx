import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import KeysPage from './pages/KeysPage';
import KeyDetailPage from './pages/KeyDetailPage';
import AlertsPage from './pages/AlertsPage';
import TeamPage from './pages/TeamPage';
import ProvidersPage from './pages/ProvidersPage';
import OnboardingPage from './pages/OnboardingPage';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/oauth/callback" element={<div className="loading-spinner"><div className="spinner" /></div>} />

          {/* Protected routes with layout */}
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/keys" element={<KeysPage />} />
            <Route path="/keys/:id" element={<KeyDetailPage />} />
            <Route path="/alerts" element={<AlertsPage />} />
            <Route path="/team" element={<TeamPage />} />
            <Route path="/providers" element={<ProvidersPage />} />
            <Route path="/onboarding" element={<OnboardingPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
