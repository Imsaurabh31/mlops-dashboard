import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Curation from './pages/Curation';
import Training from './pages/Training';
import Admin from './pages/Admin';

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/"         element={<Dashboard />} />
          <Route path="/curation" element={<Curation />}  />
          <Route path="/training" element={<Training />}  />
          <Route path="/admin"    element={<Admin />}     />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
