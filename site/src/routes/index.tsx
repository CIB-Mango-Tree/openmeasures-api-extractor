import { useEffect } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { useQueries } from '@state/query';
import { useLimitState } from '@state/limit';
import WebSocketConnection from '@lib/websocket';
import { GETQueries } from '@lib/fetch/query';
import { GETLimit } from '@lib/fetch/limit';
import Hero from '@components/hero';
import { LimitCounter, LimitAlert } from '@components/limit';
import { QueryBuilder } from '@components/builder';
import { QueryTable } from '@components/table';
import { QueryResultView } from '@components/results';
import { QueryDetailsDialog } from '@components/details';
import type { ReactElement, FC } from 'react';
import type { Query, QueryResponse } from '@appTypes/query';
import type { LimitResponse } from '@appTypes/limit';
import type { APICollectionResponse, APIResponse } from '@appTypes/fetch';
import type { QueriesState, SetQueriesCallback } from '@state/query';
import type { LimitState, SetLimitCallback } from '@state/limit';

export const Route = createFileRoute('/')({
  ssr: true,
  component: App,
})

function App(): ReactElement<FC> {
  const setQueries = useQueries((state: QueriesState): SetQueriesCallback => state.set);
  const setLimit = useLimitState((state: LimitState): SetLimitCallback => state.set);

  useEffect(() => {
    const func = async (): Promise<void> => {
      const responses: Array<PromiseSettledResult<APICollectionResponse<QueryResponse> | APIResponse<LimitResponse>>> = await Promise.allSettled([
        GETLimit(),
        GETQueries()
      ]);
      const limitResponsePromiseResult = responses[0] as PromiseSettledResult<APIResponse<LimitResponse>>;
      const apiResponsePromiseResult = responses[1] as PromiseSettledResult<APICollectionResponse<QueryResponse>>;

      if (limitResponsePromiseResult.status === 'fulfilled') setLimit({
        count: limitResponsePromiseResult.value.data.count,
        previousRequestDate: limitResponsePromiseResult.value.data.previous_request_date,
        limitRefreshDate: limitResponsePromiseResult.value.data.limit_refresh_date
      });

      if (apiResponsePromiseResult.status === 'fulfilled') setQueries(apiResponsePromiseResult.value.data.map((item: QueryResponse): Query => ({
        id: item.id,
        createdAt: item.created_at,
        updatedAt: item.updated_at,
        platform: item.platform,
        status: item.status,
        timezone: item.timezone,
        startDate: item.start_date,
        endDate: item.end_date,
        rowsFetched: item.rows_fetched,
        queriesUsed: item.queries_used,
        percentage: item.percentage,
        terms: item.terms
      })));
    };

    func();

    return (): void => {

    };
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
