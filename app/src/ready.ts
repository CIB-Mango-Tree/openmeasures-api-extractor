const POLL_INTERVAL_MS = 250;
const PROBE_TIMEOUT_MS = 2000;

function delay(ms: number): Promise<void> {
  return new Promise((resolve): void => {
    setTimeout(resolve, ms);
  });
}

// The backend is a PyInstaller onefile binary: it re-extracts itself to a temp dir on every
// launch, and on macOS a notarized binary also takes a first-run Gatekeeper scan. That can run
// to several seconds, so we wait for it to actually accept connections before pointing the user
// at a UI that would otherwise render empty.
export async function waitForBackend(url: string, timeoutMs: number): Promise<boolean> {
  const deadline: number = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    const controller: AbortController = new AbortController();
    const probeTimer: NodeJS.Timeout = setTimeout((): void => controller.abort(), PROBE_TIMEOUT_MS);

    try {
      const response: Response = await fetch(url, { signal: controller.signal });

      if (response.ok) return true;

    } catch {
      // Not listening yet (ECONNREFUSED) or still warming up. Keep polling.

    } finally {
      clearTimeout(probeTimer);
    }

    await delay(POLL_INTERVAL_MS);
  }

  return false;
}
