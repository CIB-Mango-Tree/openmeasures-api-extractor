import { useEffect } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { useQueries } from '@state/query';
import { GETQueries } from '@lib/fetch/query';
import Hero from '@components/hero';
import { LimitCounter, LimitAlert } from '@components/limit';
import { QueryBuilder } from '@components/builder';
import { QueryTable } from '@components/table';
import { QueryResultView } from '@components/results';
import { QueryDetailsDialog } from '@components/details';
import type { ReactElement, FC } from 'react';
import type { Query, QueryResponse } from '@appTypes/query';
import type { APICollectionResponse } from '@appTypes/fetch';
import type { QueriesState, SetQueriesCallback } from '@state/query';

export const Route = createFileRoute('/')({
  ssr: true,
  component: App,
})

function App(): ReactElement<FC> {
  const setQueries = useQueries((state: QueriesState): SetQueriesCallback => state.set);

  useEffect((): void => {
    const func = async (): Promise<void> => {
      const apiResponse: APICollectionResponse<QueryResponse> = await GETQueries();

      setQueries(apiResponse.data.map((item: QueryResponse): Query => ({
        id: item.id,
        createdAt: item.created_at,
        updatedAt: item.updated_at,
        platform: item.platform,
        status: item.status,
        timezone: item.timezone,
        startDate: item.start_date,
        endDate: item.end_date,
        rowsFetched: item.rows_fetched,
        percentage: item.percentage,
        terms: item.terms
      })));
    };

    func();
  }, []);

  return (
    <main className="grid grid-flow-row auto-rows-min gap-y-8 py-8 px-52">
      <Hero />
      <section className="grid grid-flow-col grid-cols-12 gap-x-4">
        <LimitAlert />
        <LimitCounter />
      </section>
      <section className="grid grid-flow-col grid-cols-12 gap-x-4">
        <QueryBuilder />
        <QueryResultView />
      </section>
      <section className="grid grid-flow-col grid-cols-12">
        <QueryTable />
      </section>
      <QueryDetailsDialog />
    </main>
  )
}
