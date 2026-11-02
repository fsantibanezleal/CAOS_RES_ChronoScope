import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router';
import App from './App';
import '@fasl-work/caos-app-shell/styles.css';
import '@fasl-work/caos-app-shell/chart.css';
import 'katex/dist/katex.min.css';
import './chronoscope.css';

// Restore a deep link captured by the Pages 404 shim (public/404.html) before the router mounts.
const redirect = sessionStorage.getItem('cs-redirect');
if (redirect && redirect !== location.pathname + location.search) {
  sessionStorage.removeItem('cs-redirect');
  history.replaceState(null, '', redirect);
}

createRoot(document.getElementById('root')!).render(
  <StrictMode><BrowserRouter basename={import.meta.env.BASE_URL}><App /></BrowserRouter></StrictMode>,
);
