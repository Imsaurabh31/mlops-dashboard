import { HashRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Curation from './pages/Curation';
import Training from './pages/Training';
import Admin from './pages/Admin';
import NotFound from './pages/NotFound';

export default function App() {
  return (
    /* HashRouter fixes deep-link 404s on static hosts (S3, GitHub Pages, nginx)
       without needing server-side rewrite rules */
    <HashRouter>
      <Layout>
        <Routes>
          <Route path="/"         element={<Dashboard />} />
          <Route path="/curation" element={<Curation />}  />
          <Route path="/training" element={<Training />}  />
          <Route path="/admin"    element={<Admin />}     />
          {/* Catch-all 404 */}
          <Route path="*"         element={<NotFound />}  />
        </Routes>
      </Layout>
    </HashRouter>
  );
}
