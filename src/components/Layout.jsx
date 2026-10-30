import { useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import './Layout.css';

// Pages that manage their own full-screen layout
const FULLSCREEN_PAGES = ['/curation'];

export default function Layout({ children }) {
  const { pathname } = useLocation();
  const isFullscreen = FULLSCREEN_PAGES.includes(pathname);

  if (isFullscreen) {
    return <div className="layout-full">{children}</div>;
  }

  return (
    <div className="layout">
      <Sidebar />
      <div className="layout__body">
        <Topbar />
        <main className="layout__main">{children}</main>
      </div>
    </div>
  );
}
