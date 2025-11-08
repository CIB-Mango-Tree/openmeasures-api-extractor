import type { QueryResponse, Query } from '@appTypes/query';
import type { LimitResponse, Limit } from '@appTypes/limit';

export function mapResponseToQuery(data: QueryResponse): Query {
  return {
    id: data.id,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    platform: data.platform,
    status: data.status,
    timezone: data.timezone,
    startDate: data.start_date,
    endDate: data.end_date,
    rowsFetched: data.rows_fetched,
    queriesUsed: data.queries_used,
    percentage: data.percentage,
    terms: data.terms
  };
}

export function mapResponseToLimit(data: LimitResponse): Limit {
  return {
    count: data.count,
    previousRequestDate: data.previous_request_date,
    limitRefreshDate: data.limit_refresh_date
  };
}
