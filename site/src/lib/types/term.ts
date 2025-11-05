import { EQ, AND, OR, NOT } from '@lib/constants/modifiers';

export type SearchTermModifier = typeof EQ | typeof AND | typeof OR | typeof NOT;

export type SearchTermValues = {
  modifier: SearchTermModifier | '';
  term: string;
};

export type SearchTermChangeValues = SearchTermValues & {
  index: string;
};
