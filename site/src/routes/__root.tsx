import { HeadContent, Scripts, createRootRoute } from '@tanstack/react-router';
import { ThemeProvider } from '@components/theme-provider';
import Header from '@components/header';
import { ModeToggle } from '@components/mode-toggle';
import appCss from '@/styles.css?url';
import type { ReactElement, FC } from 'react';

export const Route = createRootRoute({
  head: () => ({
    meta: [
      {
        charSet: 'utf-8',
      },
      {
        name: 'viewport',
        content: 'width=device-width, initial-scale=1',
      },
      {
        name: 'apple-mobile-web-app-title',
        content: 'CIB Mango Tree API Extractor'
      },
      {
        title: 'CIB Mangotree API extractor',
      },
    ],
    links: [
      {
        rel: 'stylesheet',
        href: 'https://rsms.me/inter/inter.css'
      },
      {
        rel: 'icon',
        type: 'image/png',
        sizes: '96x96',
        href: '/favicon-96x96.png'
      },
      {
        rel: 'icon',
        type: 'image/svg+xml',
        href: '/favicon.svg'
      },
      {
        rel: 'shortcut icon',
        href: '/favicon.ico'
      },
      {
        rel: 'apple-touch-icon',
        sizes: '180x180',
        href: '/apple-touch-icon.png'
      },
      {
        rel: 'manifest',
        href: '/manifest.json'
      },
      {
        rel: 'stylesheet',
        href: appCss,
      },
    ],
  }),

  shellComponent: RootDocument,
})

function RootDocument({ children }: { children: React.ReactNode }): ReactElement<FC> {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <HeadContent />
      </head>
      <body className="grid grid-flow-row grid-rows-[auto_1fr_auto] col-span-full max-w-svw min-h-svh bg-zinc-50 dark:bg-zinc-950">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <Header />
          {children}
          <footer className="grid grid-flow-col justify-end px-4 pb-4">
            <ModeToggle />
          </footer>
        </ThemeProvider>
        <Scripts />
      </body>
    </html>
  )
}
