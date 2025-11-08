import type { EventMessage } from '@appTypes/event';

export default class WebSocketConnection {
  public socket: WebSocket;
  private eventManager: EventTarget;

  constructor(url: string) {
    this.socket = new WebSocket(url);
    this.eventManager = new EventTarget();
    this.messageHandler = this.messageHandler.bind(this);

    this.socket.addEventListener("message", this.messageHandler);
  }

  private messageHandler(event: MessageEvent): void {
    if (this.eventManager == null) return;

    const message = event.data as EventMessage;

    this.eventManager.dispatchEvent(new CustomEvent(message.event, { detail: message.data }));
  }

  public on<DataType = any>(event: string, callback: (data: DataType) => void): void {
    this.eventManager.addEventListener(event, (event: Event): void => callback((event as CustomEvent).detail as DataType));
  }

  public off(event: string, callback: (data: any) => void): void {
    this.eventManager.removeEventListener(event, callback);
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
    this.socket.removeEventListener('message', this.messageHandler);
    this.socket.close();
  }
}
