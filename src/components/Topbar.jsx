import { useLocation, Link } from 'react-router-dom';
import './Topbar.css';

const PAGES = {
  '/':         { title: 'Dashboard',     sub: 'Overview of your MLOps pipeline'         },
  '/curation': { title: 'Curation',      sub: 'Annotate and verify VLM inference results' },
  '/admin':    { title: 'Admin Panel',   sub: 'Manage users, batches and curator progress' },
  '/training': { title: 'Model Training',sub: 'Train and deploy classification models'   },
};

const BREADCRUMBS = {
  '/':         [{ label: 'Home', to: '/' }],
  '/curation': [{ label: 'Home', to: '/' }, { label: 'Curation' }],
  '/admin':    [{ label: 'Home', to: '/' }, { label: 'Admin Panel' }],
  '/training': [{ label: 'Home', to: '/' }, { label: 'Training' }],
};

export default function Topbar() {
  const { pathname } = useLocation();
  const info  = PAGES[pathname]       || { title: 'MLOps', sub: '' };
  const crumbs = BREADCRUMBS[pathname] || [{ label: 'Home', to: '/' }];

  return (
    <header className="topbar">
      <div className="topbar__left">
        {/* Breadcrumb */}
        <nav className="topbar__breadcrumb" aria-label="breadcrumb">
          {crumbs.map((c, i) => (
            <span key={i} className="topbar__crumb">
              {i > 0 && <span className="topbar__crumb-sep">/</span>}
              {c.to
                ? <Link to={c.to} className="topbar__crumb-link">{c.label}</Link>
                : <span className="topbar__crumb-current">{c.label}</span>
              }
            </span>
          ))}
        </nav>
        {/* Page title */}
        <h1 className="topbar__title">{info.title}</h1>
        <p className="topbar__sub">{info.sub}</p>
      </div>

      <div className="topbar__right">
        {/* Search */}
        <div className="topbar__search">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
          <input placeholder="Search…" aria-label="Search" />
        </div>

        {/* Notifications */}
        <button className="topbar__notif" aria-label="Notifications">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0"/>
          </svg>
          <span className="topbar__notif-dot" />
        </button>

        {/* User */}
        <div className="topbar__user">
          <div className="topbar__avatar">A</div>
          <div className="topbar__user-info">
            <span className="topbar__user-name">admin</span>
            <span className="badge badge--blue" style={{ fontSize: '10px', padding: '1px 6px' }}>ADMIN</span>
          </div>
        </div>
      </div>
    </header>
  );
}
