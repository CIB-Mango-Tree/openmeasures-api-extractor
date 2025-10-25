export type SearchTermModifier = 'EQUAL' | 'AND' | 'OR';

export type SearchTermValues = {
  modifier: SearchTermModifier | '';
  term: string;
};

export type SearchTermChangeValues = SearchTermValues & {
  index: number;
};
