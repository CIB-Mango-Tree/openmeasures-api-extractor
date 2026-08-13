import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
// Self-hosted: the app runs offline as a desktop application, so the previous
// https://rsms.me/inter/inter.css link would silently fail to load.
import '@fontsource-variable/inter';
import '@/styles.css';
import App from '@/app';

const container: HTMLElement | null = document.getElementById('root');

if (container === null) throw new Error('root container is missing from index.html');

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>
);
