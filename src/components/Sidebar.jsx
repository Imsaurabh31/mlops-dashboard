import { NavLink, useNavigate } from 'react-router-dom';
import './Sidebar.css';

const NAV = [
  {
    to: '/', icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
        <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
      </svg>
    ), label: 'Dashboard',
  },
  {
    to: '/curation', icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
        <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
      </svg>
    ), label: 'Curation',
  },
  {
    to: '/admin', icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/>
      </svg>
    ), label: 'Admin Panel',
  },
  {
    to: '/training', icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
      </svg>
    ), label: 'Training',
  },
];

export default function Sidebar() {
  const navigate = useNavigate();

  return (
    <aside className="sidebar">
      {/* ── Brand — button for keyboard accessibility ── */}
      <button className="sidebar__brand" onClick={() => navigate('/')}>
        <div className="sidebar__brand-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5"/>
            <path d="M8 12l3 3 5-5" stroke="#60a5fa" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <div className="sidebar__brand-text">
          <span className="sidebar__brand-name">OLY VISION</span>
          <span className="sidebar__brand-tag">MLOps</span>
        </div>
      </button>

      {/* ── Section label ── */}
      <div className="sidebar__section-label">MENU</div>

      {/* ── Navigation ── */}
      <nav className="sidebar__nav" aria-label="Main navigation">
        {NAV.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `sidebar__link${isActive ? ' sidebar__link--active' : ''}`
            }
          >
            <span className="sidebar__link-icon" aria-hidden="true">{icon}</span>
            <span className="sidebar__link-label">{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* ── Divider ── */}
      <div className="sidebar__divider" />

      {/* ── Footer ── */}
      <div className="sidebar__footer">
        <div className="sidebar__user" aria-label="Signed in as admin">
          <div className="sidebar__avatar" aria-hidden="true">A</div>
          <div className="sidebar__user-info">
            <span className="sidebar__user-name">admin</span>
            <span className="sidebar__user-role">Administrator</span>
          </div>
        </div>
        {/* Sign out: shows a coming-soon tooltip since auth is not yet implemented */}
        <button
          className="sidebar__logout"
          title="Authentication not yet implemented"
          onClick={() => alert('Sign out will be available once authentication is implemented.')}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9"/>
          </svg>
          Sign out
        </button>
      </div>
    </aside>
  );
}
