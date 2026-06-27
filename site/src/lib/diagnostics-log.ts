import { appendFile, mkdir } from 'fs/promises';
import { homedir } from 'os';
import { join } from 'path';

// Resolve the same per-OS data dir the launcher uses (appdirsjs defaults for
// appName 'mango-tree-api-extractor'), so the frontend diagnostics log lands next to
// the backend's diagnostics.log and is retrievable from the packaged app.
function dataDir(): string {
  if (process.env.DIAGNOSTICS_LOG_DIR) return process.env.DIAGNOSTICS_LOG_DIR;

  const appName = 'mango-tree-api-extractor';
  const home = homedir();

  if (process.platform === 'darwin') return join(home, 'Library', 'Application Support', appName);
  if (process.platform === 'win32') return join(process.env.APPDATA ?? join(home, 'AppData', 'Roaming'), appName);
  return join(process.env.XDG_DATA_HOME ?? join(home, '.local', 'share'), appName);
}

const LOG_PATH = join(dataDir(), 'diagnostics-frontend.log');

export async function logDiagnostic(message: string): Promise<void> {
  const line = `${new Date().toISOString()} | frontend | ${message}\n`;

  try {
    await mkdir(dataDir(), { recursive: true });
    await appendFile(LOG_PATH, line, 'utf-8');
  } catch (err) {
    console.error('diagnostics log write failed:', err);
  }
}
