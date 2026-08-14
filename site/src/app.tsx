import { QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@components/theme-provider';
import Header from '@components/header';
import { ModeToggle } from '@components/mode-toggle';
import { TooltipProvider } from '@components/ui/tooltip';
import { queryClient } from '@lib/query-client';
import { WebSocketProvider } from '@lib/websocket-context';
import Home from '@/home';
import type { ReactElement, FC } from 'react';

// The application is a single page, so there is no router: this renders the chrome around it
// directly. The document shell, metadata and stylesheet links live in index.html.
export default function App(): ReactElement<FC> {
  return (
    <QueryClientProvider client={queryClient}>
      {/* Inside the query provider: every pushed update is written into the query cache. */}
      <WebSocketProvider>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          {/* Base UI requires an explicit Tooltip provider, and the hover delay lives here rather
              than on each tooltip -- both call sites previously passed delayDuration={1000}. */}
          <TooltipProvider delay={1000}>
            <Header />
            <Home />
            <footer className="grid grid-flow-col justify-end px-4 pb-4">
              <ModeToggle />
            </footer>
          </TooltipProvider>
        </ThemeProvider>
      </WebSocketProvider>
    </QueryClientProvider>
  );
}
