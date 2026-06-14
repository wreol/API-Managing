import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: '#' },
  { to: '/keys', label: 'Keys', icon: '*' },
  { to: '/alerts', label: 'Alerts', icon: '!' },
  { to: '/team', label: 'Team', icon: '@' },
  { to: '/providers', label: 'Providers', icon: '&' },
];

export default function Layout() {
  const { user, logout } = useAuth();

  const initials = user?.display_name
    ? user.display_name.slice(0, 2).toUpperCase()
    : (user?.email?.slice(0, 2).toUpperCase() ?? '?');

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <NavLink to="/dashboard" style={{ color: 'inherit', textDecoration: 'none' }}>
            API Vault
          </NavLink>
        </div>
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? 'active' : '')}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <NavLink to="/onboarding" style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            Setup guide
          </NavLink>
        </div>
      </aside>
      <main className="main-content">
        <header className="top-bar">
          <div className="top-bar-left">
            <span className="page-title">API Vault</span>
          </div>
          <div className="top-bar-right">
            <div className="user-info">
              <span className="user-avatar">{initials}</span>
              <span>{user?.display_name ?? user?.email}</span>
            </div>
            <button className="btn btn-ghost btn-sm" onClick={logout}>
              Log out
            </button>
          </div>
        </header>
        <Outlet />
      </main>
    </div>
  );
}
