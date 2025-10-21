export type BaseResponse = {
  code: number;
};


export type APIResponse<DataType> = BaseResponse & {
  data: DataType;
};

export type APICollectionResponse<DataType> = BaseResponse & {
  count: number;
  data: Array<DataType>;
};

export type APIErrorResponse<Err> = BaseResponse & {
  error: Err;
};

export type APIErrorCollectionResponse<Err> = BaseResponse & {
  error: Array<Err>;
};
