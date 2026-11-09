import { useLocation, Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import './Topbar.css';

const PAGES = {
  '/':         { title: 'Dashboard',      sub: 'Overview of your MLOps pipeline'           },
  '/curation': { title: 'Curation',       sub: 'Annotate and verify VLM inference results'  },
  '/admin':    { title: 'Admin Panel',    sub: 'Manage users, batches and curator progress' },
  '/training': { title: 'Model Training', sub: 'Train and deploy classification models'     },
};

const BREADCRUMBS = {
  '/':         [{ label: 'Home', to: '/' }],
  '/curation': [{ label: 'Home', to: '/' }, { label: 'Curation' }],
  '/admin':    [{ label: 'Home', to: '/' }, { label: 'Admin Panel' }],
  '/training': [{ label: 'Home', to: '/' }, { label: 'Training' }],
};

/* Quick-nav: map search terms to routes */
const SEARCH_ROUTES = [
  { terms: ['dashboard', 'home', 'overview'],     to: '/'         },
  { terms: ['curation', 'annotate', 'gallery'],    to: '/curation' },
  { terms: ['admin', 'batch', 'user'],             to: '/admin'    },
  { terms: ['training', 'model', 'train', 'deploy'], to: '/training' },
];

export default function Topbar() {
  const { pathname } = useLocation();
  const navigate     = useNavigate();
  const [query, setQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);

  const info   = PAGES[pathname]       || { title: 'MLOps', sub: '' };
  const crumbs = BREADCRUMBS[pathname] || [{ label: 'Home', to: '/' }];

  const suggestions = query.length > 0
    ? SEARCH_ROUTES.filter(r =>
        r.terms.some(t => t.includes(query.toLowerCase()))
      )
    : [];

  const handleSearch = (e) => {
    e.preventDefault();
    if (suggestions.length > 0) {
      navigate(suggestions[0].to);
      setQuery('');
      setShowSuggestions(false);
    }
  };

  return (
    <header className="topbar">
      <div className="topbar__left">
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
        <h1 className="topbar__title">{info.title}</h1>
        <p className="topbar__sub">{info.sub}</p>
      </div>

      <div className="topbar__right">
        {/* Functional search — navigates to matching page */}
        <form className="topbar__search" onSubmit={handleSearch} style={{ position: 'relative' }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
          <input
            placeholder="Search pages…"
            aria-label="Search pages"
            value={query}
            onChange={e => { setQuery(e.target.value); setShowSuggestions(true); }}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
            onFocus={() => query && setShowSuggestions(true)}
          />
          {showSuggestions && suggestions.length > 0 && (
            <div className="topbar__suggestions">
              {suggestions.map(s => (
                <button
                  key={s.to}
                  type="button"
                  className="topbar__suggestion"
                  onMouseDown={() => { navigate(s.to); setQuery(''); setShowSuggestions(false); }}
                >
                  {s.terms[0].charAt(0).toUpperCase() + s.terms[0].slice(1)}
                </button>
              ))}
            </div>
          )}
        </form>

        {/* User */}
        <div className="topbar__user" role="status" aria-label="Signed in as admin">
          <div className="topbar__avatar" aria-hidden="true">A</div>
          <div className="topbar__user-info">
            <span className="topbar__user-name">admin</span>
            <span className="badge badge--blue" style={{ fontSize: '10px', padding: '1px 6px' }}>ADMIN</span>
          </div>
        </div>
      </div>
    </header>
  );
}
