import { createServer, connect } from 'net';
import chalk from 'chalk';
import type { Server, Socket } from 'net';

// macOS (and most dual-stack systems) resolve `localhost` to BOTH ::1 and 127.0.0.1, with the
// IPv6 address listed first. Nitro's node-server can only bind a single address, and binding
// `::` would expose the app to the LAN, so we bind 127.0.0.1 and put a loopback-only forwarder
// on [::1] instead. It is a raw TCP pipe, so it carries plain HTTP and WebSocket upgrades alike.
export function startLoopbackForwarder(port: number, targetHost: string): Promise<Server | null> {
  return new Promise((resolve): void => {
    const server: Server = createServer((client: Socket): void => {
      const upstream: Socket = connect({ host: targetHost, port });
      const teardown = (): void => {
        client.destroy();
        upstream.destroy();
      };

      client.on('error', teardown);
      upstream.on('error', teardown);
      client.pipe(upstream);
      upstream.pipe(client);
    });

    server.once('error', (err: NodeJS.ErrnoException): void => {
      // Not fatal: 127.0.0.1 still works, and so does `localhost` on any host whose resolver
      // prefers IPv4. Losing the forwarder only costs us the IPv6-first case.
      console.warn(chalk.yellow(`🥭 IPv6 loopback forwarder unavailable (${err.code ?? err.message}); http://[::1]:${port} will not resolve.`));
      resolve(null);
    });

    server.listen({ host: '::1', port }, (): void => {
      server.on('error', (err: NodeJS.ErrnoException): void => {
        console.warn(chalk.yellow(`🥭 IPv6 loopback forwarder error: ${err.code ?? err.message}`));
      });
      resolve(server);
    });
  });
}
