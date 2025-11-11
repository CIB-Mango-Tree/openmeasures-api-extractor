export type EventMessageData = {
  message?: string;
  [index: string]: any;
};

export type EventMessage = {
  event: string;
  data: EventMessageData;
};
