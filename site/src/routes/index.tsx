import { createFileRoute } from '@tanstack/react-router';
import Hero from '@components/hero';
import { LimitCounter, LimitAlert } from '@components/limit';
import { QueryBuilder, QueryResultView } from '@components/query';
import type { ReactElement, FC } from 'react';

export const Route = createFileRoute('/')({
  ssr: true,
  component: App,
})

function App(): ReactElement<FC> {
  return (
    <main className="grid grid-flow-row auto-rows-min gap-y-8 pt-8 px-52">
      <Hero />
      <section className="grid grid-flow-col grid-cols-12 gap-x-4">
        <LimitAlert />
        <LimitCounter />
      </section>
      <section className="grid grid-flow-col grid-cols-12 gap-x-4">
        <QueryBuilder />
        <QueryResultView />
      </section>
      <section className="grid grid-flow-col"></section>
    </main>
  )
}
