export type LimitResponse = {
  count: number;
  previous_request_date: Date | null;
  limit_refresh_date: Date | null;
};

export type Limit = {
  count: number;
  previousRequestDate: Date | null;
  limitRefreshDate: Date | null;
};
