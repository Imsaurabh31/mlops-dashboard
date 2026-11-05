import { useNavigate } from 'react-router-dom';

export default function NotFound() {
  const navigate = useNavigate();
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', height: '60vh', gap: 16, textAlign: 'center',
    }}>
      <div style={{ fontSize: 48 }}>404</div>
      <h2 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>
        Page not found
      </h2>
      <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>
        The page you are looking for does not exist.
      </p>
      <button className="btn btn--primary" onClick={() => navigate('/')}>
        ← Back to Dashboard
      </button>
    </div>
  );
}
