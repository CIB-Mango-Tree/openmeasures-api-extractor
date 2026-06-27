import { getRequestURL, getRequestHeader } from 'h3';
import { logDiagnostic } from '../lib/diagnostics-log';
import type { NitroApp } from 'nitropack';
import type { H3Event } from 'h3';

// Registered as a Nitro plugin so the 'request' hook fires for EVERY request,
// including /api/** ones handled by the routeRules proxy (which bypasses h3
// middleware). This is what lets us capture the inbound client address family
// (::1 vs 127.0.0.1) for the localhost/IPv6 dual-stack hypothesis.
export default (nitroApp: NitroApp): void => {
  nitroApp.hooks.hook('request', (event: H3Event): void => {
    const url = getRequestURL(event);

    if (!url.pathname.startsWith('/api')) return;

    const socket = event.node?.req?.socket;

    logDiagnostic(
      `http ${event.method} ${url.pathname} ` +
      `host=${getRequestHeader(event, 'host')} ` +
      `origin=${getRequestHeader(event, 'origin')} ` +
      `xff=${getRequestHeader(event, 'x-forwarded-for')} ` +
      `remote=${socket?.remoteAddress} family=${socket?.remoteFamily}`
    );
  });
};
