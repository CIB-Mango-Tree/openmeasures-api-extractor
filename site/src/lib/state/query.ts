import { create } from 'zustand';
import { Query } from '@appTypes/query';

export interface SelectedQueryState {
  selected: Query | null;
  select: (query: Query) => void;
  unSelect: () => void;
}

export const useSelectedQuery = create<SelectedQueryState>((setState): SelectedQueryState => ({
  selected: null,
  select: (query: Query): void => setState((state: SelectedQueryState): SelectedQueryState => ({ ...state, selected: query })),
  unSelect: (): void => setState((state: SelectedQueryState): SelectedQueryState => ({ ...state, selected: null }))
}));
