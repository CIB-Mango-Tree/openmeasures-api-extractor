import type { EventMessage } from '@appTypes/event';

export default class WebSocketConnection {
  private socket: WebSocket;
  private eventManager: EventTarget;
  private messageHandler: (event: MessageEvent) => void;

  constructor(socket: WebSocket) {
    this.socket = socket;
    this.eventManager = new EventTarget();
    this.messageHandler = (event: MessageEvent): void => {
      const message = event.data as EventMessage;

      this.eventManager.dispatchEvent(new CustomEvent(message.event, { detail: message.data }));
    };

    this.socket.addEventListener("message", this.messageHandler);
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
