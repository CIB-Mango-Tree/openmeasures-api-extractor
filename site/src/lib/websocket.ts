import type { EventMessage, EventMessageData } from '@appTypes/event';

const BASE_RECONNECT_DELAY_MS = 1000;
const MAX_RECONNECT_DELAY_MS = 30_000;

export type WebSocketConnectionHandlers = {
  onOpen?: (reconnected: boolean) => void;
  onDisconnect?: () => void;
};

export default class WebSocketConnection {
  private url: string;
  private eventManager: EventTarget;
  // Aborted only by close(). A transport error must never tear this down, or every consumer
  // callback registered through on() dies with it and the page goes permanently deaf.
  private controller: AbortController;
  // Scoped to a single socket, so abandoning one on reconnect detaches its listeners and drops
  // the reference to it. Sharing the consumer controller here would retain every dead socket.
  private socketController: AbortController;
  private handlers: WebSocketConnectionHandlers;
  private topics: Set<string>;
  private closedByConsumer: boolean;
  private reconnectAttempts: number;
  private reconnectTimer: ReturnType<typeof setTimeout> | null;
  private hasConnected: boolean;
  public socket: WebSocket;

  constructor(url: string, handlers: WebSocketConnectionHandlers = {}) {
    this.url = url;
    this.eventManager = new EventTarget();
    this.controller = new AbortController();
    this.socketController = new AbortController();
    this.handlers = handlers;
    this.topics = new Set<string>();
    this.closedByConsumer = false;
    this.reconnectAttempts = 0;
    this.reconnectTimer = null;
    this.hasConnected = false;

    this.messageHandler = this.messageHandler.bind(this);
    this.openHandler = this.openHandler.bind(this);
    this.closeHandler = this.closeHandler.bind(this);
    this.errorHandler = this.errorHandler.bind(this);

    this.socket = this.connect();
  }

  private connect(): WebSocket {
    this.socketController.abort();
    this.socketController = new AbortController();

    const options: AddEventListenerOptions = { signal: this.socketController.signal };
    const socket: WebSocket = new WebSocket(this.url);

    socket.addEventListener('message', this.messageHandler, options);
    socket.addEventListener('open', this.openHandler, options);
    socket.addEventListener('close', this.closeHandler, options);
    socket.addEventListener('error', this.errorHandler, options);

    return socket;
  }

  private openHandler(): void {
    const reconnected: boolean = this.hasConnected;

    this.reconnectAttempts = 0;
    this.hasConnected = true;

    // Subscriptions live on the server side of the socket, so a reconnected socket knows nothing
    // about them. Without this replay the progress view silently stops updating after a blip.
    for (const topic of this.topics) {
      this.send('SUBSCRIBE', topic);
    }

    this.handlers.onOpen?.(reconnected);
  }

  private messageHandler(event: MessageEvent): void {
    let message: EventMessage;

    try {
      message = JSON.parse(event.data) as EventMessage;

    } catch {
      return;
    }

    if (message.event == null) return;

    this.eventManager.dispatchEvent(new CustomEvent(message.event, { detail: message.data }));
  }

  // Errors are informational only. The browser always fires 'close' after a socket fails, so
  // reconnection is driven from there alone and cannot be triggered twice for one failure.
  private errorHandler(): void {
    this.handlers.onDisconnect?.();
  }

  private closeHandler(): void {
    if (this.closedByConsumer) return;

    this.handlers.onDisconnect?.();

    const exponential: number = Math.min(
      BASE_RECONNECT_DELAY_MS * 2 ** this.reconnectAttempts,
      MAX_RECONNECT_DELAY_MS
    );
    const wait: number = exponential * (0.75 + Math.random() * 0.5);

    this.reconnectAttempts += 1;
    this.reconnectTimer = setTimeout((): void => {
      this.reconnectTimer = null;

      if (this.closedByConsumer) return;

      this.socket = this.connect();
    }, wait);
  }

  private send(action: string, topic: string): void {
    if (this.socket.readyState !== WebSocket.OPEN) return;

    this.socket.send(JSON.stringify({ action, topic }));
  }

  public on(event: string, callback: (data: EventMessageData) => void): void {
    this.eventManager.addEventListener(
      event,
      (event: Event): void => callback((event as CustomEvent).detail as EventMessageData),
      { signal: this.controller.signal }
    );
  }

  public off(event: string, callback: (data: any) => void): void {
    this.eventManager.removeEventListener(event, callback);
  }

  public subscribe(topic: string): void {
    this.topics.add(topic);
    this.send('SUBSCRIBE', topic);
  }

  public unsubscribe(topic: string): void {
    this.topics.delete(topic);
    this.send('UNSUBSCRIBE', topic);
  }

  public close(): void {
    this.closedByConsumer = true;

    if (this.reconnectTimer != null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    this.socketController.abort();
    this.controller.abort();
    this.socket.close();
  }
}
