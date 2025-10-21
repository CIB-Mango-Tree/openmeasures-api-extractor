import { create } from 'zustand';
import type { Limit } from '@appTypes/limit';

export interface LimitState {
  count: number;
  previousRequestDate: Date | null;
  limitRefreshDate: Date | null;
  set: (limit: Limit) => void;
}

export const useLimitState = create<LimitState>((setState): LimitState => ({
  count: 39,
  previousRequestDate: null,
  limitRefreshDate: null,
  set: (limit: Limit): void => setState((state: LimitState): LimitState => ({ ...limit, ...state }))
}));
