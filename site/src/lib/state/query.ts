import { create } from 'zustand';
import { Query } from '@appTypes/query';

export interface FetchingQueryState {
  query: Query | null;
  showProgress: boolean;
  setQuery: (query: Query) => void;
  removeQuery: () => void;
  toggleShow: () => void;
}

export interface QueriesState {
  queries: Array<Query>;
  set: (queries: Array<Query>) => void;
  push: (query: Query) => void;
  update: (query: Query) => void;
}

export const useFetchingQueryState = create<FetchingQueryState>((setState): FetchingQueryState => ({
  query: null,
  showProgress: false,
  setQuery: (query: Query): void => setState((state: FetchingQueryState): FetchingQueryState => ({ ...state, query })),
  removeQuery: (): void => setState((state: FetchingQueryState): FetchingQueryState => ({ ...state, query: null })),
  toggleShow: (): void => setState((state: FetchingQueryState): FetchingQueryState => ({ ...state, showProgress: !state.showProgress }))
}));

export const useQueries = create<QueriesState>((setState): QueriesState => ({
  queries: [],
  set: (queries: Array<Query>): void => setState((state: QueriesState): QueriesState => ({ ...state, queries })),
  push: (query: Query): void => setState((state: QueriesState): QueriesState => ({ ...state, queries: [...state.queries, query] })),
  update: (query: Query): void => setState((state: QueriesState): QueriesState => ({
    ...state,
    queries: state.queries.map((item: Query) => query.id === item.id ? query : item)
  })),
}))
