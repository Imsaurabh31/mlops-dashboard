/**
 * ProtectedRoute — redirects to /login if not authenticated.
 * Also shows a 403 if the user lacks permission for the page.
 */
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';

export default function ProtectedRoute({ children, page }) {
  const { user, loading } = useAuth();
  const location          = useLocation();

  if (loading) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        height: '60vh', color: 'var(--text-muted)', fontSize: 14,
      }}>
        Verifying session…
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  /* Role check */
  if (page) {
    const perms = {
      admin:   ['dashboard', 'curation', 'training', 'admin', 'deployment'],
      curator: ['dashboard', 'curation', 'training'],
      viewer:  ['dashboard', 'deployment'],
    };
    if (!(perms[user.role] || []).includes(page)) {
      return (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', height: '60vh', gap: 12, textAlign: 'center',
        }}>
          <div style={{ fontSize: 40 }}>🔒</div>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>
            Access Denied
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>
            Your role <strong>{user.role}</strong> does not have access to this page.
          </p>
          <button className="btn btn--primary" onClick={() => window.history.back()}>
            ← Go Back
          </button>
        </div>
      );
    }
  }

  return children;
}
