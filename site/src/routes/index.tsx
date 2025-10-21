import { createFileRoute } from '@tanstack/react-router';
import Hero from '@components/hero';
import type { ReactElement, FC } from 'react';

export const Route = createFileRoute('/')({
  ssr: true,
  component: App,
})

function App(): ReactElement<FC> {
  return (
    <main className="grid grid-flow-col px-20 pt-8">
      <Hero />
      <section className="grid grid-flow-col"></section>
      <section className="grid grid-flow-col"></section>
      <section className="grid grid-flow-col"></section>
    </main>
  )
}
