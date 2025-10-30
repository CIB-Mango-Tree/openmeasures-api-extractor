import { create } from 'zustand';
import { Query } from '@appTypes/query';

export type SetQueriesCallback = (queries: Array<Query>) => void;
export type QueryCallback = (query: Query) => void;

export interface SelectedQueryState {
  selectedQuery: Query | null;
  set: QueryCallback;
  clear: () => void;
}

export interface FetchingQueryState {
  query: Query | null;
  showProgress: boolean;
  setQuery: QueryCallback;
  removeQuery: () => void;
  toggleShow: () => void;
}

export interface QueriesState {
  queries: Array<Query>;
  set: SetQueriesCallback;
  push: QueryCallback;
  update: QueryCallback;
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
}));

export const useSelectedQuery = create<SelectedQueryState>((setState): SelectedQueryState => ({
  selectedQuery: null,
  set: (query: Query): void => setState((state: SelectedQueryState): SelectedQueryState => ({ ...state, selectedQuery: query })),
  clear: (): void => setState((state: SelectedQueryState): SelectedQueryState => ({ ...state, selectedQuery: null }))
}));
