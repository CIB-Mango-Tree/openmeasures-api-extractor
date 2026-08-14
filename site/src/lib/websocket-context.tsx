import { createContext, useCallback, useContext, useEffect, useMemo, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import WebSocketConnection from '@lib/websocket';
import { cacheQuery, cacheLimit } from '@lib/api';
import { mapResponseToQuery, mapResponseToLimit } from '@lib/map';
import { useFetchingQueryState, useSelectedQuery } from '@state/query';
import { useLimitAlertState } from '@state/limit';
import {
  FETCH_UPDATE_PROGRESS,
  PARSE_IN_PROGRESS,
  FETCH_INCOMPLETE,
  PARSE_INCOMPLETE,
  QUERY_COMPLETE,
  LIMIT_UPDATE,
  LIMIT_MAXED_OUT,
} from '@constants/status';
import type { ReactElement, ReactNode, FC } from 'react';
import type { QueryClient } from '@tanstack/react-query';
import type { Query, QueryResponse } from '@appTypes/query';
import type { LimitResponse } from '@appTypes/limit';
import type { EventMessageData } from '@appTypes/event';
import type { FetchingQueryState, SelectedQueryState } from '@state/query';
import type { LimitAlertState } from '@state/limit';

const INCOMPLETE_FETCH_MESSAGE = 'data fetch is imcomplete. user must approve finishing the query to continue';

export type WebSocketContextValue = {
  subscribe: (topic: string) => void;
  unsubscribe: (topic: string) => void;
};

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

export function useWebSocket(): WebSocketContextValue {
  const value: WebSocketContextValue | null = useContext(WebSocketContext);

  if (value == null) throw new Error('useWebSocket must be used inside a WebSocketProvider');

  return value;
}

/**
 * Owns the single connection to the update stream and routes every pushed event into the query
 * cache.
 *
 * Updates are pushed, not polled: this is the only thing that keeps the progress bar and the
 * limit counter live during an extraction. Subscriptions are reference counted because more than
 * one component can care about the same query at once -- the details dialog and an in-flight
 * export, for instance -- and a blunt unsubscribe from one would silence the other.
 */
export function WebSocketProvider({ children }: { children: ReactNode; }): ReactElement<FC> {
  const queryClient: QueryClient = useQueryClient();
  const connectionRef = useRef<WebSocketConnection | null>(null);
  const topicCountsRef = useRef<Map<string, number>>(new Map());

  /**
   * Drops a topic outright, whatever is still holding it.
   *
   * Used when a query completes: nothing further will ever be pushed for it, so keeping the
   * subscription would leak a topic on the server for the rest of the session. Holders that
   * release afterwards find a count of zero and no-op.
   */
  const releaseTopic = useCallback((topic: string): void => {
    if (!topicCountsRef.current.has(topic)) return;

    topicCountsRef.current.delete(topic);
    connectionRef.current?.unsubscribe(topic);
  }, []);

  useEffect((): (() => void) => {
    const wsProtocol: string = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const connection = new WebSocketConnection(
      `${wsProtocol}://${window.location.host}/api/ws/updates`
    );

    connectionRef.current = connection;

    // Every pushed update lands in the query cache and nowhere else, so the table, the progress
    // card and the details dialog all read the same object rather than three copies of it.
    connection.on(FETCH_UPDATE_PROGRESS, (data: EventMessageData): void => {
      cacheQuery(queryClient, mapResponseToQuery(data as QueryResponse));
    });
    connection.on(PARSE_IN_PROGRESS, (data: EventMessageData): void => {
      cacheQuery(queryClient, mapResponseToQuery(data.query as QueryResponse));
    });
    connection.on(PARSE_INCOMPLETE, (data: EventMessageData): void => {
      cacheQuery(queryClient, mapResponseToQuery(data.query as QueryResponse));
    });
    connection.on(FETCH_INCOMPLETE, (data: EventMessageData): void => {
      const query: Query = mapResponseToQuery(data.query as QueryResponse);

      cacheQuery(queryClient, query);

      if (
        useFetchingQueryState.getState().queryID === query.id &&
        data.message === INCOMPLETE_FETCH_MESSAGE
      ) {
        const alertState: LimitAlertState = useLimitAlertState.getState();

        alertState.setType('continue');
        if (!alertState.show) alertState.toggleShow();
      }
    });
    connection.on(QUERY_COMPLETE, (data: EventMessageData): void => {
      const query: Query = mapResponseToQuery(data.query as QueryResponse);
      const fetchingState: FetchingQueryState = useFetchingQueryState.getState();
      const selectedState: SelectedQueryState = useSelectedQuery.getState();

      // Cached before releasing the topic, so anything waiting on this query sees the final
      // state. Watchers read the cache, not the socket, so dropping the subscription here
      // cannot cost them the update.
      cacheQuery(queryClient, query);
      // COMPLETE is the one genuinely terminal status. The INCOMPLETE statuses deliberately keep
      // their subscription: those queries can be resumed in place, and the resume reuses the same
      // id, so releasing here would leave the retry with no progress updates.
      releaseTopic(query.id);

      if (fetchingState.queryID === query.id && fetchingState.showProgress) fetchingState.toggleShow();
      if (selectedState.selectedQueryID === query.id) selectedState.setCurrentView('complete');

      toast.success('Extraction Complete', { description: `Data extraction for ${query.platform} is complete!` });
    });
    connection.on(LIMIT_UPDATE, (data: EventMessageData): void => {
      cacheLimit(queryClient, mapResponseToLimit(data as LimitResponse));
    });
    connection.on(LIMIT_MAXED_OUT, (data: EventMessageData): void => {
      const alertState: LimitAlertState = useLimitAlertState.getState();
      const fetchingState: FetchingQueryState = useFetchingQueryState.getState();
      const selectedState: SelectedQueryState = useSelectedQuery.getState();

      cacheLimit(queryClient, mapResponseToLimit(data.limit as LimitResponse));
      alertState.setType('maxed_out');
      if (!alertState.show) alertState.toggleShow();

      if (fetchingState.queryID != null) {
        if (fetchingState.showProgress) fetchingState.toggleShow();
        fetchingState.removeQuery();
      }

      if (selectedState.selectedQueryID != null && selectedState.currentView === 'progress') {
        selectedState.setCurrentView('details');
      }
    });

    return (): void => {
      connection.close();
      connectionRef.current = null;
      topicCountsRef.current.clear();
    };
  }, [queryClient, releaseTopic]);

  const subscribe = useCallback((topic: string): void => {
    const next: number = (topicCountsRef.current.get(topic) ?? 0) + 1;

    topicCountsRef.current.set(topic, next);

    // The server tracks one subscription per topic, so only the first holder needs to ask.
    if (next === 1) connectionRef.current?.subscribe(topic);
  }, []);

  const unsubscribe = useCallback((topic: string): void => {
    const current: number = topicCountsRef.current.get(topic) ?? 0;

    if (current === 0) return;

    if (current > 1) {
      topicCountsRef.current.set(topic, current - 1);
      return;
    }

    topicCountsRef.current.delete(topic);
    connectionRef.current?.unsubscribe(topic);
  }, []);

  const value = useMemo<WebSocketContextValue>(
    (): WebSocketContextValue => ({ subscribe, unsubscribe }),
    [subscribe, unsubscribe]
  );

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>;
}
