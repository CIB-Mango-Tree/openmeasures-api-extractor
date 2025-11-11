import type { EventMessage, EventMessageData } from '@appTypes/event';

export default class WebSocketConnection {
  private url: string;
  public socket: WebSocket;

  constructor(url: string) {
    this.url = url;
    this.socket = new WebSocket(this.url);
    this.messageHandler = this.messageHandler.bind(this);
    this.reconnectHandler = this.reconnectHandler.bind(this);
    this.errorHandler = this.errorHandler.bind(this);

    this.socket.addEventListener('message', this.messageHandler);
    this.socket.addEventListener('close', this.reconnectHandler);
    this.socket.addEventListener('error', this.errorHandler);
  }

  private messageHandler(event: MessageEvent): void {
    const message = JSON.parse(event.data) as EventMessage;

    if (message.event == null) return;

    this.socket.dispatchEvent(new CustomEvent(message.event, { detail: message.data }));
  }

  private reconnectHandler(): void {
    setTimeout((): void => {
      this.socket = new WebSocket(this.url);

      this.socket.addEventListener('message', this.messageHandler);
      this.socket.addEventListener('close', this.reconnectHandler);
      this.socket.addEventListener('error', this.errorHandler);
    }, 1000);
  }

  private errorHandler(): void {
    this.close();
  }

  public on(event: string, callback: (data: EventMessageData) => void): void {
    this.socket.addEventListener(event, (event: Event): void => callback((event as CustomEvent).detail as EventMessageData));
  }

  public off(event: string, callback: (data: any) => void): void {
    this.socket.removeEventListener(event, callback);
  }

  public subscribe(topic: string): void {
    if (this.socket.readyState !== WebSocket.OPEN) {
      this.socket.addEventListener('open', (): void => {
        this.socket.send(JSON.stringify({
          action: 'SUBSCRIBE',
          topic
        }));
      }, { once: true });
      return;
    }

    this.socket.send(JSON.stringify({
      action: 'SUBSCRIBE',
      topic
    }));
  }

  public unsubscribe(topic: string): void {
    if (this.socket.readyState !== WebSocket.OPEN) {
      this.socket.addEventListener('open', (): void => {
        this.socket.send(JSON.stringify({
          action: 'UNSUBSCRIBE',
          topic
        }));
      }, { once: true });
      return;
    }

    this.socket.send(JSON.stringify({
      action: 'UNSUBSCRIBE',
      topic
    }));
  }

  public close(): void {
    this.socket.removeEventListener('close', this.reconnectHandler);
    this.socket.removeEventListener('error', this.errorHandler);
    this.socket.removeEventListener('message', this.messageHandler);
    this.socket.close();
  }
}
