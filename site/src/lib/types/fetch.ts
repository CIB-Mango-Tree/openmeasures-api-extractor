export type APIResponse<DataType> = {
  code: number;
  data: DataType;
};

export type APICollectionResponse<DataType> = {
  code: number;
  count: number;
  data: Array<DataType>;
};
