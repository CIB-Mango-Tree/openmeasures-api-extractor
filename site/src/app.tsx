import { ThemeProvider } from '@components/theme-provider';
import Header from '@components/header';
import { ModeToggle } from '@components/mode-toggle';
import Home from '@/home';
import type { ReactElement, FC } from 'react';

// The application is a single page, so there is no router: this renders the chrome around it
// directly. The document shell, metadata and stylesheet links live in index.html.
export default function App(): ReactElement<FC> {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <Header />
      <Home />
      <footer className="grid grid-flow-col justify-end px-4 pb-4">
        <ModeToggle />
      </footer>
    </ThemeProvider>
  );
}
