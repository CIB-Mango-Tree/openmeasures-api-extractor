import { create } from 'zustand';
import type { Limit } from '@appTypes/limit';

export type SetLimitCallback = (limit: Limit) => void;

export interface LimitState {
  count: number;
  previousRequestDate: Date | null;
  limitRefreshDate: Date | null;
  set: SetLimitCallback;
}

export const useLimitState = create<LimitState>((setState): LimitState => ({
  count: 39,
  previousRequestDate: null,
  limitRefreshDate: null,
  set: (limit: Limit): void => setState((state: LimitState): LimitState => ({ ...state, ...limit }))
}));
