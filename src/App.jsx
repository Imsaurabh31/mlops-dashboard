import { HashRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard  from './pages/Dashboard';
import Curation   from './pages/Curation';
import Training   from './pages/Training';
import Admin      from './pages/Admin';
import Deployment from './pages/Deployment';
import NotFound   from './pages/NotFound';

export default function App() {
  return (
    <HashRouter>
      <Layout>
        <Routes>
          <Route path="/"           element={<Dashboard />}  />
          <Route path="/curation"   element={<Curation />}   />
          <Route path="/training"   element={<Training />}   />
          <Route path="/admin"      element={<Admin />}      />
          <Route path="/deployment" element={<Deployment />} />
          <Route path="*"           element={<NotFound />}   />
        </Routes>
      </Layout>
    </HashRouter>
  );
}
