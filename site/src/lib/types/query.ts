import { FETCH_IN_PROGRESS, FETCH_INCOMPLETE, CLEAN_IN_PROGRESS, CLEAN_INCOMPLETE, PARSE_IN_PROGRESS, PARSE_INCOMPLETE, QUERY_COMPLETE } from '@constants/status';
import { SearchTermModifier } from '@appTypes/term';

export type QueryTerm = {
  term: string;
  modifier: SearchTermModifier;
};

export type QueryStatus = typeof FETCH_IN_PROGRESS | typeof FETCH_INCOMPLETE | typeof CLEAN_IN_PROGRESS | typeof CLEAN_INCOMPLETE | typeof PARSE_IN_PROGRESS | typeof PARSE_INCOMPLETE | typeof QUERY_COMPLETE;

export type Query = {
  id: string;
  createdAt: Date;
  updatedAt: Date | null;
  platform: string;
  status: QueryStatus;
  timezone: string;
  startDate: Date;
  endDate: Date;
  rowsFetched: number;
  queriesUsed: number;
  percentage: number;
  terms: Array<QueryTerm>;
};

export type QueryResponse = {
  id: string;
  created_at: Date;
  updated_at: Date | null;
  platform: string;
  status: QueryStatus;
  timezone: string;
  start_date: Date;
  end_date: Date;
  rows_fetched: number;
  queries_used: number;
  percentage: number;
  terms: Array<QueryTerm>;
};

export type CreateQueryPayload = {
  timezone: string;
  start_date: string;
  end_date: string;
  platform: string;
  terms: Array<QueryTerm>;
};
