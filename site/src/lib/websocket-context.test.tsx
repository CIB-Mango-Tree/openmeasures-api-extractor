import { describe, expect, test, vi, beforeEach, afterEach } from 'vitest';
import { render, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { WebSocketProvider, useWebSocket } from '@lib/websocket-context';
import { queryKeys } from '@lib/api';
import { QUERY_COMPLETE, PARSE_IN_PROGRESS, FETCH_INCOMPLETE } from '@constants/status';
import type { ReactElement } from 'react';
import type { Query } from '@appTypes/query';
import type { WebSocketContextValue } from '@lib/websocket-context';

class FakeSocket extends EventTarget {
  static OPEN = 1;
  static instances: Array<FakeSocket> = [];

  public readyState: number = FakeSocket.OPEN;
  public sent: Array<{ action: string; topic: string; }> = [];

  constructor(public url: string) {
    super();

    FakeSocket.instances.push(this);
  }

  send(raw: string): void {
    this.sent.push(JSON.parse(raw));
  }

  close(): void {
    this.readyState = 3;
  }

  /** Delivers a frame exactly as the backend would. */
  push(event: string, data: unknown): void {
    act((): void => {
      this.dispatchEvent(new MessageEvent('message', { data: JSON.stringify({ event, data }) }));
    });
  }

  framesFor(action: string, topic: string): number {
    return this.sent.filter((frame): boolean => frame.action === action && frame.topic === topic).length;
  }
}

function queryPayload(id: string, status: string, updatedAt: string): Record<string, unknown> {
  return {
    id,
    created_at: '2026-08-13T00:00:00',
    updated_at: updatedAt,
    platform: 'bluesky',
    status,
    timezone: 'UTC',
    start_date: '2026-08-01T00:00:00',
    end_date: '2026-08-02T00:00:00',
    rows_fetched: 10,
    queries_used: 1,
    percentage: 0.4,
    terms: [],
  };
}

let client: QueryClient;
let api: WebSocketContextValue;

function Probe(): ReactElement {
  api = useWebSocket();

  return <div />;
}

function renderProvider(): void {
  render(
    <QueryClientProvider client={client}>
      <WebSocketProvider>
        <Probe />
      </WebSocketProvider>
    </QueryClientProvider>
  );
}

function socket(): FakeSocket {
  return FakeSocket.instances[FakeSocket.instances.length - 1];
}

function cached(id: string): Query | undefined {
  return client.getQueryData<Array<Query>>(queryKeys.queries)?.find(
    (item: Query): boolean => item.id === id
  );
}

beforeEach((): void => {
  FakeSocket.instances = [];
  vi.stubGlobal('WebSocket', FakeSocket);
  client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  client.setQueryData(queryKeys.queries, []);
});

afterEach((): void => {
  vi.unstubAllGlobals();
});

describe('pushed updates', (): void => {
  test('a progress event lands in the query cache', async (): Promise<void> => {
    renderProvider();

    socket().push(PARSE_IN_PROGRESS, {
      query: queryPayload('q1', PARSE_IN_PROGRESS, '2026-08-13T10:00:00'),
    });

    await waitFor((): void => {
      expect(cached('q1')?.status).toBe(PARSE_IN_PROGRESS);
    });
  });

  test('an older update does not overwrite a newer one', async (): Promise<void> => {
    // The PATCH reply and the socket race; a slow response must not resurrect a stale status.
    renderProvider();

    socket().push(QUERY_COMPLETE, {
      query: queryPayload('q1', QUERY_COMPLETE, '2026-08-13T10:00:05'),
    });

    await waitFor((): void => {
      expect(cached('q1')?.status).toBe(QUERY_COMPLETE);
    });

    socket().push(PARSE_IN_PROGRESS, {
      query: queryPayload('q1', PARSE_IN_PROGRESS, '2026-08-13T10:00:01'),
    });

    expect(cached('q1')?.status).toBe(QUERY_COMPLETE);
  });
});

describe('subscriptions', (): void => {
  test('the server is asked once no matter how many holders there are', (): void => {
    renderProvider();

    act((): void => {
      api.subscribe('q1');
      api.subscribe('q1');
    });

    expect(socket().framesFor('SUBSCRIBE', 'q1')).toBe(1);
  });

  test('releasing one holder leaves the other subscribed', (): void => {
    renderProvider();

    act((): void => {
      api.subscribe('q1');
      api.subscribe('q1');
      api.unsubscribe('q1');
    });

    expect(socket().framesFor('UNSUBSCRIBE', 'q1')).toBe(0);

    act((): void => {
      api.unsubscribe('q1');
    });

    expect(socket().framesFor('UNSUBSCRIBE', 'q1')).toBe(1);
  });

  test('completion unsubscribes, since nothing more will ever be pushed', (): void => {
    renderProvider();

    act((): void => {
      api.subscribe('q1');
    });

    socket().push(QUERY_COMPLETE, { query: queryPayload('q1', QUERY_COMPLETE, '2026-08-13T10:00:00') });

    expect(socket().framesFor('UNSUBSCRIBE', 'q1')).toBe(1);
  });

  test('a release after completion is a no-op rather than an underflow', (): void => {
    renderProvider();

    act((): void => {
      api.subscribe('q1');
    });

    socket().push(QUERY_COMPLETE, { query: queryPayload('q1', QUERY_COMPLETE, '2026-08-13T10:00:00') });

    act((): void => {
      api.unsubscribe('q1');
    });

    expect(socket().framesFor('UNSUBSCRIBE', 'q1')).toBe(1);
  });

  test('an incomplete query keeps its subscription so a resume still reports progress', (): void => {
    // The resume reuses the same id, so dropping the topic here would silence the retry.
    renderProvider();

    act((): void => {
      api.subscribe('q1');
    });

    socket().push(FETCH_INCOMPLETE, {
      query: queryPayload('q1', FETCH_INCOMPLETE, '2026-08-13T10:00:00'),
      message: 'something else',
    });

    expect(socket().framesFor('UNSUBSCRIBE', 'q1')).toBe(0);
  });
});
