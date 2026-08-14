import { useEffect, useRef } from 'react';
import { toast } from 'sonner';
import { useFetchingQueryState, useSelectedQuery } from '@state/query';
import { useQueryList, useLimitQuery, useQueryByID } from '@lib/api';
import { useWebSocket } from '@lib/websocket-context';
import Hero from '@components/hero';
import { LimitCounter, LimitAlert, LimitAlertDialog } from '@components/limit';
import { QueryBuilder } from '@components/builder';
import { QueryTable } from '@components/table';
import { QueryResultView } from '@components/results';
import { QueryDetailsDialog } from '@components/details';
import { Toaster } from '@components/ui/sonner';
import { QUERY_COMPLETE } from '@constants/status';
import { FETCHING_QUERY_KEY, SELECTED_QUERY_KEY } from '@constants/local-storage';
import type { ReactElement, FC } from 'react';
import type { Query } from '@appTypes/query';
import type { FetchingQueryState, SelectedQueryState } from '@state/query';

export default function Home(): ReactElement<FC> {
  const queriesResult = useQueryList();
  const limitResult = useLimitQuery();
  const { subscribe, unsubscribe } = useWebSocket();
  const fetchingQueryState = useFetchingQueryState((state: FetchingQueryState): FetchingQueryState => state);
  const selectedQueryState = useSelectedQuery((state: SelectedQueryState): SelectedQueryState => state);
  const fetchingQuery: Query | null = useQueryByID(fetchingQueryState.queryID);
  const selectedQuery: Query | null = useQueryByID(selectedQueryState.selectedQueryID);
  const restoredRef = useRef<boolean>(false);
  const loadFailureReportedRef = useRef<boolean>(false);

  // Restoring from localStorage has to wait for the query list: it looks queries up by id, so
  // running it while the read was still in flight meant the lookup always missed and the saved
  // ids were deleted on every single mount.
  useEffect((): void => {
    if (restoredRef.current || !queriesResult.isSuccess) return;

    restoredRef.current = true;

    const queries: Array<Query> = queriesResult.data;
    const fetchingQueryID: string | null = window.localStorage.getItem(FETCHING_QUERY_KEY);
    const selectedQueryID: string | null = window.localStorage.getItem(SELECTED_QUERY_KEY);
    const findRestorable = (id: string): Query | undefined => queries.find(
      (item: Query): boolean => item.id === id && item.status !== QUERY_COMPLETE
    );

    if (fetchingQueryID != null) {
      if (findRestorable(fetchingQueryID) != null) {
        const fetchingState: FetchingQueryState = useFetchingQueryState.getState();

        fetchingState.setQueryID(fetchingQueryID);
        if (!fetchingState.showProgress) fetchingState.toggleShow();

      } else {
        window.localStorage.removeItem(FETCHING_QUERY_KEY);
      }
    }

    if (selectedQueryID != null) {
      if (findRestorable(selectedQueryID) != null) {
        const selectedState: SelectedQueryState = useSelectedQuery.getState();

        selectedState.setQueryID(selectedQueryID);
        selectedState.setCurrentView('progress');

      } else {
        window.localStorage.removeItem(SELECTED_QUERY_KEY);
      }
    }
  }, [queriesResult.isSuccess, queriesResult.data]);

  // Retries are exhausted by the time isError is set, so a backend that never came up would
  // otherwise just leave the page looking empty. One toast, not one per failed read.
  useEffect((): void => {
    if (loadFailureReportedRef.current) return;
    if (!queriesResult.isError && !limitResult.isError) return;

    loadFailureReportedRef.current = true;

    console.error('Initial data load failed:', [queriesResult.error, limitResult.error].filter(Boolean));
    toast.error('Could not load your extractions', {
      description: 'The extractor service is not responding yet. It may still be starting up.'
    });
  }, [queriesResult.isError, limitResult.isError, queriesResult.error, limitResult.error]);

  // Progress for a query only arrives while its topic is subscribed, so the subscription follows
  // whichever query the UI is watching. The id is persisted alongside it, so closing the window
  // mid-extraction resumes the same view on the next launch.
  useEffect((): (() => void) | void => {
    const id: string | null = fetchingQueryState.queryID;

    if (id == null) {
      window.localStorage.removeItem(FETCHING_QUERY_KEY);
      return;
    }

    window.localStorage.setItem(FETCHING_QUERY_KEY, id);
    subscribe(id);

    return (): void => unsubscribe(id);
  }, [fetchingQueryState.queryID, subscribe, unsubscribe]);

  useEffect((): (() => void) | void => {
    const id: string | null = selectedQueryState.selectedQueryID;

    if (id == null) {
      window.localStorage.removeItem(SELECTED_QUERY_KEY);
      return;
    }

    window.localStorage.setItem(SELECTED_QUERY_KEY, id);
    subscribe(id);

    return (): void => unsubscribe(id);
  }, [selectedQueryState.selectedQueryID, subscribe, unsubscribe]);

  // A completed query has nothing left to push, and the provider has already dropped its topic.
  useEffect((): void => {
    if (fetchingQuery?.status === QUERY_COMPLETE) window.localStorage.removeItem(FETCHING_QUERY_KEY);
    if (selectedQuery?.status === QUERY_COMPLETE) window.localStorage.removeItem(SELECTED_QUERY_KEY);
  }, [fetchingQuery?.status, selectedQuery?.status]);

  return (
    <main className="grid grid-flow-row auto-rows-min gap-y-4 py-8 px-52">
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
      <Toaster position="top-right" closeButton />
    </main>
  )
}
