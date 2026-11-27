import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import './Login.css';

const DEMO_ACCOUNTS = [
  { role: 'Admin',   email: 'admin@oly.com',   password: 'admin123',   color: '#7c3aed' },
  { role: 'Curator', email: 'alice@oly.com',   password: 'curator123', color: '#2563eb' },
  { role: 'Viewer',  email: 'viewer@oly.com',  password: 'viewer123',  color: '#0891b2' },
];

export default function Login() {
  const { login }    = useAuth();
  const navigate     = useNavigate();
  const location     = useLocation();
  const from         = location.state?.from?.pathname || '/';

  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = (acc) => {
    setEmail(acc.email);
    setPassword(acc.password);
    setError('');
  };

  return (
    <div className="login">
      <div className="login__card">
        {/* Brand */}
        <div className="login__brand">
          <div className="login__brand-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5"/>
              <path d="M8 12l3 3 5-5" stroke="#60a5fa" strokeWidth="2.5"
                strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div>
            <h1 className="login__title">OLY VISION</h1>
            <p className="login__subtitle">MLOps Dashboard</p>
          </div>
        </div>

        <h2 className="login__heading">Sign in to your account</h2>

        {/* Error */}
        {error && (
          <div className="login__error" role="alert">
            ⚠ {error}
          </div>
        )}

        {/* Form */}
        <form className="login__form" onSubmit={handleSubmit} noValidate>
          <div className="login__field">
            <label className="login__label" htmlFor="email">Email</label>
            <input
              id="email"
              className="login__input"
              type="email"
              placeholder="you@oly.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              autoComplete="email"
              autoFocus
            />
          </div>

          <div className="login__field">
            <label className="login__label" htmlFor="password">Password</label>
            <input
              id="password"
              className="login__input"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            className="login__btn"
            disabled={loading}
          >
            {loading ? 'Signing in…' : 'Sign in →'}
          </button>
        </form>

        {/* Demo accounts */}
        <div className="login__demo">
          <p className="login__demo-label">Demo accounts</p>
          <div className="login__demo-cards">
            {DEMO_ACCOUNTS.map(acc => (
              <button
                key={acc.role}
                className="login__demo-card"
                style={{ '--demo-color': acc.color }}
                onClick={() => fillDemo(acc)}
                type="button"
              >
                <span className="login__demo-role">{acc.role}</span>
                <span className="login__demo-email">{acc.email}</span>
              </button>
            ))}
          </div>
          <p className="login__demo-hint">
            Click a card to fill credentials, then click Sign in
          </p>
        </div>
      </div>
    </div>
  );
}
