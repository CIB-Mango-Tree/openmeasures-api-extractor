import { useEffect, useRef } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { useQueries, useFetchingQueryState, useSelectedQuery } from '@state/query';
import { useLimitState } from '@state/limit';
import WebSocketConnection from '@lib/websocket';
import { GETQueries } from '@lib/fetch/query';
import { GETLimit } from '@lib/fetch/limit';
import { mapResponseToQuery, mapResponseToLimit } from '@lib/map';
import Hero from '@components/hero';
import { LimitCounter, LimitAlert, LimitAlertDialog } from '@components/limit';
import { QueryBuilder } from '@components/builder';
import { QueryTable } from '@components/table';
import { QueryResultView } from '@components/results';
import { QueryDetailsDialog } from '@components/details';
import { FETCH_UPDATE_PROGRESS, FETCH_INCOMPLETE, QUERY_COMPLETE, LIMIT_UPDATE, LIMIT_MAXED_OUT } from '@constants/status';
import { FETCHING_QUERY_KEY, SELECTED_QUERY_KEY } from '@constants/local-storage';
import type { ReactElement, FC } from 'react';
import type { Query, QueryResponse } from '@appTypes/query';
import type { Limit, LimitResponse } from '@appTypes/limit';
import type { APICollectionResponse, APIResponse } from '@appTypes/fetch';
import type { FetchingQueryState, QueriesState } from '@state/query';
import type { LimitState } from '@state/limit';

export const Route = createFileRoute('/')({
  ssr: true,
  component: App,
})

function App(): ReactElement<FC> {
  const queriesState = useQueries((state: QueriesState): QueriesState => state);
  const limitState = useLimitState((state: LimitState): LimitState => state);
  const fetchingQueryState = useFetchingQueryState((state: FetchingQueryState): FetchingQueryState => state);
  const connectionRef = useRef<WebSocketConnection | null>(null);

  useEffect(() => {
    const func = async (): Promise<void> => {
      const responses: Array<PromiseSettledResult<APICollectionResponse<QueryResponse> | APIResponse<LimitResponse>>> = await Promise.allSettled([
        GETLimit(),
        GETQueries()
      ]);
      const limitResponsePromiseResult = responses[0] as PromiseSettledResult<APIResponse<LimitResponse>>;
      const apiResponsePromiseResult = responses[1] as PromiseSettledResult<APICollectionResponse<QueryResponse>>;

      if (limitResponsePromiseResult.status === 'fulfilled') limitState.set(mapResponseToLimit(limitResponsePromiseResult.value.data));
      if (apiResponsePromiseResult.status === 'fulfilled') queriesState.set(apiResponsePromiseResult.value.data.map((item: QueryResponse): Query => mapResponseToQuery(item)));
    };

    func();

    connectionRef.current = new WebSocketConnection(
      `${import.meta.env.VITE_API_URL.replace('http', 'ws')}/api/ws/updates`
    );

    connectionRef.current.on(FETCH_UPDATE_PROGRESS, (data: any) => {
      const query: Query = mapResponseToQuery(data);
      const fetchingState = useFetchingQueryState.getState();
      const selectedQueryState = useSelectedQuery.getState();
      const queriesState = useQueries.getState();

      if (fetchingState.query?.id === query.id) fetchingState.setQuery(query);
      if (selectedQueryState.selectedQuery?.id === query.id) selectedQueryState.setQuery(query);

      queriesState.update(query);
    });

    connectionRef.current.on(FETCH_INCOMPLETE, (data: any) => {
      const query: Query = mapResponseToQuery(data);

      const fetchingState = useFetchingQueryState.getState();
      const queriesState = useQueries.getState();
      const selectedQueryState = useSelectedQuery.getState();
      const limitState = useLimitState.getState();

      if (fetchingState.query?.id === query.id) {
        fetchingState.setQuery(query);
        limitState.toggleLimitAlertDialog();
      }

      if (selectedQueryState.selectedQuery?.id === query.id) {
        selectedQueryState.setQuery(query);
        limitState.toggleLimitAlertDialog();
      }

      queriesState.update(query);
    });

    connectionRef.current.on(QUERY_COMPLETE, (data: QueryResponse): void => {
      const query: Query = mapResponseToQuery(data);

      const fetchingState = useFetchingQueryState.getState();
      const queriesState = useQueries.getState();

      if (fetchingState.query?.id === query.id) {
        fetchingState.setQuery(query);
      }
      queriesState.update(query);
    });

    connectionRef.current.on(LIMIT_UPDATE, (data: LimitResponse): void => {
      const limitState = useLimitState.getState();

      limitState.set(mapResponseToLimit(data));
    });

    connectionRef.current.on(LIMIT_MAXED_OUT, (data: LimitResponse): void => {
      const limitState = useLimitState.getState();

      limitState.set(mapResponseToLimit(data));
      limitState.toggleLimitAlertDialog();
    });

    const fetchingQueryID: string | null = window.localStorage.getItem(FETCHING_QUERY_KEY);
    const selectedQueryID: string | null = window.localStorage.getItem(SELECTED_QUERY_KEY);

    if (fetchingQueryID != null) {
      const queriesState = useQueries.getState();
      const query = queriesState.queries.find((item: Query): boolean => item.id === fetchingQueryID);

      if (query != null && query.status !== QUERY_COMPLETE) {
        const fetchingState = useFetchingQueryState.getState();

        fetchingState.setQuery(query);
        fetchingState.toggleShow();
        connectionRef.current.subscribe(fetchingQueryID);

      } else {
        window.localStorage.removeItem(FETCHING_QUERY_KEY);
      }
    }

    if (selectedQueryID != null) {
      const queriesState = useQueries.getState();
      const query = queriesState.queries.find((item: Query): boolean => item.id === selectedQueryID);

      if (query != null && query.status !== QUERY_COMPLETE) {
        const fetchingState = useFetchingQueryState.getState();

        fetchingState.setQuery(query);
        fetchingState.toggleShow();
        connectionRef.current.subscribe(selectedQueryID);

      } else {
        window.localStorage.removeItem(FETCHING_QUERY_KEY);
      }
    }

    return (): void => {
      if (connectionRef.current != null) connectionRef.current.close();
    };
  }, []);


  useEffect((): void => {
    if (connectionRef.current == null) return;

    const currentStoredID = window.localStorage.getItem(FETCHING_QUERY_KEY);
    const fetchingState = useFetchingQueryState.getState();

    if (fetchingState.query != null) {
      const newID = fetchingState.query.id;

      if (currentStoredID !== newID) {
        if (currentStoredID) connectionRef.current.unsubscribe(currentStoredID);

        window.localStorage.setItem(FETCHING_QUERY_KEY, newID);
        connectionRef.current.subscribe(newID);
      }

      return;
    }

    if (fetchingState.query == null && currentStoredID != null) {
      connectionRef.current.unsubscribe(currentStoredID);
      window.localStorage.removeItem(FETCHING_QUERY_KEY);
    }
  }, [fetchingQueryState.query]);

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
      <LimitAlertDialog />
    </main>
  )
}
