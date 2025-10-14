import { FETCH_IN_PROGRESS, FETCH_INCOMPLETE, CLEAN_IN_PROGRESS, CLEAN_INCOMPLETE, PARSE_IN_PROGRESS, PARSE_INCOMPLETE, QUERY_COMPLETE } from '@constants/status';

export type QueryTerm = {
  term: string;
  modifier: 'EQUAL' | 'AND' | 'OR';
};

export type QueryRequest = {
  rowCount: number;
  requests: Array<{ [index: string]: any; }>;
};

export type Query = {
  id: string;
  createdAt: Date;
  updatedAt: Date | null;
  platform: string;
  status: typeof FETCH_IN_PROGRESS | typeof FETCH_INCOMPLETE | typeof CLEAN_IN_PROGRESS | typeof CLEAN_INCOMPLETE | typeof PARSE_IN_PROGRESS | typeof PARSE_INCOMPLETE | typeof QUERY_COMPLETE;
  timezone: string;
  startDate: Date;
  endDate: Date;
  rowsFetched: number;
  percentage: number;
  terms: Array<QueryTerm>;
  requests: Array<QueryRequest>;
};
