import type { EventMessage, EventMessageData } from '@appTypes/event';

export default class WebSocketConnection {
  public socket: WebSocket;

  constructor(url: string) {
    this.socket = new WebSocket(url);
    this.messageHandler = this.messageHandler.bind(this);

    this.socket.addEventListener("message", this.messageHandler);
  }

  private messageHandler(event: MessageEvent): void {
    const message = JSON.parse(event.data) as EventMessage;

    if (message.event == null) return;

    this.socket.dispatchEvent(new CustomEvent(message.event, { detail: message.data }));
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
    this.socket.removeEventListener('message', this.messageHandler);
    this.socket.close();
  }
}
