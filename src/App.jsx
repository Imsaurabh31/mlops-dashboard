import { HashRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import ProtectedRoute  from './auth/ProtectedRoute';
import Layout      from './components/Layout';
import Login       from './pages/Login';
import Dashboard   from './pages/Dashboard';
import Curation    from './pages/Curation';
import Training    from './pages/Training';
import Admin       from './pages/Admin';
import Deployment  from './pages/Deployment';
import NotFound    from './pages/NotFound';

export default function App() {
  return (
    <HashRouter>
      <AuthProvider>
        <Routes>
          {/* Public route */}
          <Route path="/login" element={<Login />} />

          {/* Protected routes — all wrapped in Layout */}
          <Route path="/" element={
            <ProtectedRoute page="dashboard">
              <Layout><Dashboard /></Layout>
            </ProtectedRoute>
          } />
          <Route path="/curation" element={
            <ProtectedRoute page="curation">
              <Layout><Curation /></Layout>
            </ProtectedRoute>
          } />
          <Route path="/training" element={
            <ProtectedRoute page="training">
              <Layout><Training /></Layout>
            </ProtectedRoute>
          } />
          <Route path="/admin" element={
            <ProtectedRoute page="admin">
              <Layout><Admin /></Layout>
            </ProtectedRoute>
          } />
          <Route path="/deployment" element={
            <ProtectedRoute page="deployment">
              <Layout><Deployment /></Layout>
            </ProtectedRoute>
          } />

          <Route path="*" element={<Layout><NotFound /></Layout>} />
        </Routes>
      </AuthProvider>
    </HashRouter>
  );
}
