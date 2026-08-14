import { create } from 'zustand';

export type LimitAlertType = 'continue' | 'maxed_out';

// The limit counter itself is server state and lives in the TanStack Query cache (useLimit in
// @lib/api). Only the alert's visibility is local UI state.

export interface LimitAlertState {
  show: boolean;
  type: LimitAlertType;
  toggleShow: () => void;
  setType: (type: LimitAlertType) => void;
}

export const useLimitAlertState = create<LimitAlertState>((setState): LimitAlertState => ({
  show: false,
  type: 'continue',
  toggleShow: (): void => setState((state: LimitAlertState): LimitAlertState => ({ ...state, show: !state.show })),
  setType: (type: LimitAlertType): void => setState((state: LimitAlertState): LimitAlertState => ({ ...state, type }))
}));
