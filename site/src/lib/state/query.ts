import { create } from 'zustand';
import { Query } from '@appTypes/query';

export type ShowExportState = 'export' | 'progress';

export interface SelectedQueryState {
  selected: Query | null;
  select: (query: Query) => void;
  unSelect: () => void;
}

export interface FetchingQueryState {
  query: Query | null;
  show: 'export' | 'progress';
  setQuery: (query: Query) => void;
  removeQuery: () => void;
  setShowState: (showState: ShowExportState) => void;
}

export const useSelectedQuery = create<SelectedQueryState>((setState): SelectedQueryState => ({
  selected: null,
  select: (query: Query): void => setState((state: SelectedQueryState): SelectedQueryState => ({ ...state, selected: query })),
  unSelect: (): void => setState((state: SelectedQueryState): SelectedQueryState => ({ ...state, selected: null }))
}));

export const useFetchingQueryState = create<FetchingQueryState>((setState): FetchingQueryState => ({
  query: null,
  show: 'export',
  setQuery: (query: Query): void => setState((state: FetchingQueryState): FetchingQueryState => ({ ...state, query })),
  removeQuery: (): void => setState((state: FetchingQueryState): FetchingQueryState => ({ ...state, query: null })),
  setShowState: (showState: ShowExportState): void => setState((state: FetchingQueryState): FetchingQueryState => ({ ...state, show: showState }))
}));
