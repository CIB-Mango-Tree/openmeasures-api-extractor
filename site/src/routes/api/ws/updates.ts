import { defineWebSocketHandler } from 'h3';
import type { Peer } from 'crossws';

const BACKEND_WS_URL = 'ws://127.0.0.1:8000/api/ws/updates';

interface ProxyState {
  backend: WebSocket;
  backlog: string[];
}

const stateByPeer = new WeakMap<Peer, ProxyState>();

export default defineWebSocketHandler({
  open(peer) {
    const backend = new WebSocket(BACKEND_WS_URL);
    const state: ProxyState = { backend, backlog: [] };
    stateByPeer.set(peer, state);

    backend.addEventListener('open', () => {
      for (const msg of state.backlog) backend.send(msg);
      state.backlog = [];
    });

    backend.addEventListener('message', (event: MessageEvent) => {
      peer.send(typeof event.data === 'string' ? event.data : (event.data as ArrayBuffer));
    });

    backend.addEventListener('close', () => {
      try { peer.close(); } catch { /* peer already closed */ }
      stateByPeer.delete(peer);
    });

    backend.addEventListener('error', (event) => {
      console.error('WS proxy: backend error', event);
      try { peer.close(1011, 'backend error'); } catch { /* peer already closed */ }
      stateByPeer.delete(peer);
    });
  },

  message(peer, message) {
    const state = stateByPeer.get(peer);
    if (!state) return;
    const text = message.text();
    if (state.backend.readyState === WebSocket.OPEN) {
      state.backend.send(text);
    } else {
      state.backlog.push(text);
    }
  },

  close(peer) {
    const state = stateByPeer.get(peer);
    if (!state) return;
    try { state.backend.close(); } catch { /* backend already closed */ }
    stateByPeer.delete(peer);
  },

  error(peer, error) {
    console.error('WS proxy: peer error', error);
    const state = stateByPeer.get(peer);
    if (!state) return;
    try { state.backend.close(); } catch { /* backend already closed */ }
    stateByPeer.delete(peer);
  },
});
