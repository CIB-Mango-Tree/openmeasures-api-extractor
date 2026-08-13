import { readFile, writeFile, stat, mkdir, rm } from 'fs/promises';
import { existsSync } from 'fs';
import { join, dirname } from 'path';
import { spawn } from 'child_process';
import { createHash } from 'crypto';
import appDirs from 'appdirsjs';
import chalk from 'chalk';
import { copyDir } from './dir';
import { startLoopbackForwarder } from './forwarder';
import { waitForBackend } from './ready';
import type { Server } from 'net';
import type { ChildProcess } from 'child_process';
import type { Stats } from 'fs';

const NITRO_HOST = '127.0.0.1';
const NITRO_PORT = 3000;
const BACKEND_HOST = '127.0.0.1';
const BACKEND_PORT = 8000;

// PyInstaller onefile re-extracts a ~65MB archive on every launch, and a notarized binary also
// takes a first-run Gatekeeper scan. Slow machines have been observed well past 30s.
const BACKEND_READY_TIMEOUT_MS = 120_000;

const BUNDLE_DIRS = ['.output', '.nitro', 'dist'] as const;

export interface StartResult {
  uiUrl: string;
  apiUrl: string;
  dataDir: string;
  backendDataDir: string;
}

function resolveBackendPath(): string {
  const override: string | undefined = process.env.MANGO_BACKEND_PATH;

  if (override != null && override.length > 0) return override;

  const binaryName: string = process.platform === 'win32'
    ? 'mango-tree-api-extractor-backend.exe'
    : 'mango-tree-api-extractor-backend';

  // Every installer drops the launcher and the backend into the same directory, so a sibling
  // lookup keeps working when the user picks a non-default install location (the NSIS directory
  // page lets them) or moves the folder. The absolute paths below are only the fallback.
  const sibling: string = join(dirname(process.execPath), binaryName);

  if (existsSync(sibling)) return sibling;

  if (process.platform === 'darwin') {
    return join('/Applications', 'mango-tree-extractor', binaryName);
  }

  if (
    process.platform === 'linux' ||
    process.platform === 'netbsd' ||
    process.platform === 'freebsd' ||
    process.platform === 'openbsd'
  ) {
    return join('/usr/local/bin', binaryName);
  }

  if (process.platform === 'win32') {
    return join(process.env.ProgramFiles ?? 'C:\\Program Files', 'mango-tree-extractor', binaryName);
  }

  throw Error('unsupported platform...');
}

// copyDir only ever writes, so without clearing first an in-place upgrade leaves the user running
// a mix of old and new server chunks. Only runs when the runtime hash changed.
async function refreshBundle(bundlePath: string, dataPath: string): Promise<void> {
  await mkdir(dataPath, { recursive: true });

  for (const dir of BUNDLE_DIRS) {
    await rm(join(dataPath, dir), { recursive: true, force: true });
  }

  const writeOperations: Array<PromiseSettledResult<void>> = await Promise.allSettled(
    BUNDLE_DIRS.map((dir: string): Promise<void> => copyDir(join(bundlePath, dir), join(dataPath, dir)))
  );

  for (const operation of writeOperations) {
    if (operation.status === 'rejected') throw Error(operation.reason);
  }
}

export async function start(): Promise<StartResult> {
  const appDirectories = appDirs({ appName: 'mango-tree-api-extractor' });
  const backendDirectories = appDirs({ appName: 'mango-tree-api-extractor-backend' });
  const runtimeStats: Stats = await stat(process.execPath);
  const runtimeHash: string = createHash('md5')
    .update(`${runtimeStats.size}-${runtimeStats.mtimeMs}`)
    .digest('hex')
    .slice(0, 8);
  const cacheHashFilePath: string = join(appDirectories.data, '.cache-hash');
  const currentHash: string | null = existsSync(cacheHashFilePath) ? (await readFile(cacheHashFilePath)).toString() : null;
  const bundlePath: string = join(__dirname, '..', 'bundle');

  if (runtimeHash !== currentHash) {
    await refreshBundle(bundlePath, appDirectories.data);
    await writeFile(cacheHashFilePath, runtimeHash, { encoding: 'utf-8' });
  }

  const backendPath: string = resolveBackendPath();
  const uiUrl: string = `http://${NITRO_HOST}:${NITRO_PORT}`;
  const apiUrl: string = `http://${BACKEND_HOST}:${BACKEND_PORT}/api`;

  const backendProcess: ChildProcess = spawn(backendPath, { stdio: 'inherit' });
  const frontendProcess: ChildProcess = spawn(process.execPath, [join(appDirectories.data, '.output', 'server', 'index.mjs')], {
    env: { ...process.env, NITRO_HOST, NITRO_PORT: String(NITRO_PORT) },
    stdio: 'inherit',
  });

  let forwarder: Server | null = null;

  backendProcess.on('error', (err): void => {
    console.error(chalk.red(`Failed to start backend at ${backendPath}:`), err);
    process.exit(1);
  });

  backendProcess.on('exit', (code, signal): void => {
    if (code !== 0 && code !== null) {
      console.error(chalk.red(`Backend exited with code ${code} (signal ${signal})`));
      process.exit(1);
    }
  });

  frontendProcess.on('error', (err): void => {
    console.error(chalk.red('Failed to start the frontend server:'), err);
    process.exit(1);
  });

  frontendProcess.on('exit', (code, signal): void => {
    if (code !== 0 && code !== null) {
      console.error(chalk.red(`Frontend server exited with code ${code} (signal ${signal}). Is port ${NITRO_PORT} already in use?`));
      process.exit(1);
    }
  });

  const handleKill = (): void => {
    console.log(chalk.bold.white('\n🥭 Shutting down API extractor...\n'));
    forwarder?.close();
    frontendProcess.kill();
    backendProcess.kill();
    process.exit();
  };

  process.on('SIGINT', handleKill);
  process.on('SIGTERM', handleKill);

  forwarder = await startLoopbackForwarder(NITRO_PORT, NITRO_HOST);

  console.log(chalk.cyan(`🥭 Waiting for the backend to finish starting up (this can take a moment on first launch)...`));

  const ready: boolean = await waitForBackend(`${apiUrl}/health`, BACKEND_READY_TIMEOUT_MS);

  if (!ready) {
    console.warn(chalk.yellow(
      `🥭 The backend did not respond within ${Math.round(BACKEND_READY_TIMEOUT_MS / 1000)}s. ` +
      `The UI will keep retrying, but if it stays empty check the diagnostics logs listed below.`
    ));
  }

  return {
    uiUrl,
    apiUrl,
    dataDir: appDirectories.data,
    backendDataDir: backendDirectories.data,
  };
}
