"use client";

import { ThemeProvider as NextThemesProvider } from 'next-themes';
import type { ReactElement, FC, ComponentProps } from 'react';

export function ThemeProvider({
  children,
  ...props
}: ComponentProps<typeof NextThemesProvider>): ReactElement<FC> {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>
}
