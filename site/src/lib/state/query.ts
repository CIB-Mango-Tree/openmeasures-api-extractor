import { create } from 'zustand';

export type CurrentViewType = 'details' | 'progress' | 'complete';

// These stores hold which query the UI is pointing at, not the query itself: the query objects
// live in the TanStack Query cache (see @lib/api). Keeping copies here meant every WebSocket
// handler had to write the same update into three places to keep them from drifting apart.

export interface SelectedQueryState {
  selectedQueryID: string | null;
  currentView: CurrentViewType;
  setQueryID: (id: string) => void;
  removeQuery: () => void;
  setCurrentView: (view: CurrentViewType) => void;
  clear: () => void;
}

export interface FetchingQueryState {
  queryID: string | null;
  showProgress: boolean;
  setQueryID: (id: string) => void;
  removeQuery: () => void;
  toggleShow: () => void;
}

export const useFetchingQueryState = create<FetchingQueryState>((setState): FetchingQueryState => ({
  queryID: null,
  showProgress: false,
  setQueryID: (id: string): void => setState((state: FetchingQueryState): FetchingQueryState => ({ ...state, queryID: id })),
  removeQuery: (): void => setState((state: FetchingQueryState): FetchingQueryState => ({ ...state, queryID: null })),
  toggleShow: (): void => setState((state: FetchingQueryState): FetchingQueryState => ({ ...state, showProgress: !state.showProgress }))
}));

export const useSelectedQuery = create<SelectedQueryState>((setState): SelectedQueryState => ({
  selectedQueryID: null,
  currentView: 'details',
  setQueryID: (id: string): void => setState((state: SelectedQueryState): SelectedQueryState => ({ ...state, selectedQueryID: id })),
  removeQuery: (): void => setState((state: SelectedQueryState): SelectedQueryState => ({ ...state, selectedQueryID: null })),
  setCurrentView: (view: CurrentViewType): void => setState((state: SelectedQueryState): SelectedQueryState => ({ ...state, currentView: view })),
  clear: (): void => setState((state: SelectedQueryState): SelectedQueryState => ({ ...state, currentView: 'details', selectedQueryID: null }))
}));
