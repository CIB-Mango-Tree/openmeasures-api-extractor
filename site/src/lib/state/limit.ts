import { create } from 'zustand';
import type { Limit } from '@appTypes/limit';

export type SetLimitCallback = (limit: Limit) => void;
export type LimitAlertType = 'continue' | 'maxed_out';

export interface LimitState {
  count: number;
  previousRequestDate: Date | null;
  limitRefreshDate: Date | null;
  set: SetLimitCallback;
};

export interface LimitAlertState {
  show: boolean;
  type: LimitAlertType;
  toggleShow: () => void;
  setType: (type: LimitAlertType) => void;
}

export const useLimitState = create<LimitState>((setState): LimitState => ({
  count: 39,
  previousRequestDate: null,
  limitRefreshDate: null,
  set: (limit: Limit): void => setState((state: LimitState): LimitState => ({ ...state, ...limit })),
}));

export const useLimitAlertState = create<LimitAlertState>((setState): LimitAlertState => ({
  show: false,
  type: 'continue',
  toggleShow: (): void => setState((state: LimitAlertState): LimitAlertState => ({ ...state, show: !state.show })),
  setType: (type: LimitAlertType): void => setState((state: LimitAlertState): LimitAlertState => ({ ...state, type }))
}))
