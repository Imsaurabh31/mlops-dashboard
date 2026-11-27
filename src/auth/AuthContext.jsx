/**
 * AuthContext — provides user, token, login, logout across the whole app.
 * Token is stored in localStorage so it survives page refresh.
 */
import { createContext, useContext, useState, useEffect, useCallback } from 'react';

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser]   = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('oly_token'));
  const [loading, setLoading] = useState(true);

  /* On mount, verify stored token is still valid */
  useEffect(() => {
    if (!token) { setLoading(false); return; }

    fetch(`${BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : null)
      .then(u => {
        if (u) setUser(u);
        else { localStorage.removeItem('oly_token'); setToken(null); }
      })
      .catch(() => { localStorage.removeItem('oly_token'); setToken(null); })
      .finally(() => setLoading(false));
  }, []); // eslint-disable-line

  const login = useCallback(async (email, password) => {
    const res = await fetch(`${BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Login failed');
    }

    const data = await res.json();
    localStorage.setItem('oly_token', data.access_token);
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('oly_token');
    setToken(null);
    setUser(null);
  }, []);

  /* Check if user has access to a page */
  const can = useCallback((page) => {
    if (!user) return false;
    const perms = {
      admin:   ['dashboard', 'curation', 'training', 'admin', 'deployment', 'users'],
      curator: ['dashboard', 'curation', 'training'],
      viewer:  ['dashboard', 'deployment'],
    };
    return (perms[user.role] || []).includes(page);
  }, [user]);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, can }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}

export default AuthContext;
