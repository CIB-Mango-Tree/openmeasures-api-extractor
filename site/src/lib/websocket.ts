import type { EventMessage } from '@appTypes/event';

export default class WebSocketConnection {
  public socket: WebSocket;
  private eventManager: EventTarget;

  constructor(url: string) {
    this.socket = new WebSocket(url);
    this.eventManager = new EventTarget();

    this.socket.addEventListener("message", this.messageHandler);
  }

  private messageHandler(event: MessageEvent): void {
    const message = event.data as EventMessage;

    this.eventManager.dispatchEvent(new CustomEvent(message.event, { detail: message.data }));
  }

  public on(event: string, callback: (event: Event) => void): void {
    this.eventManager.addEventListener(event, callback);
  }

  public off(event: string, callback: (event: Event) => void): void {
    this.eventManager.removeEventListener(event, callback);
  }

  public subscribe(topic: string): void {
    this.socket.send(JSON.stringify({
      action: 'SUBSCRIBE',
      topic
    }));
  }

  public unsubscribe(topic: string): void {
    this.socket.send(JSON.stringify({
      action: 'UNSUBSCRIBE',
      topic
    }))
  }

  public close(): void {
    this.socket.removeEventListener('message', this.messageHandler);
    this.socket.close();
  }
}
