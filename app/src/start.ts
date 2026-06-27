import { readFile, writeFile, stat, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import { join } from 'path';
import { spawn } from 'child_process';
import { createHash } from 'crypto';
import appDirs from 'appdirsjs';
import chalk from 'chalk';
import { copyDir } from './dir';
import type { ChildProcess } from 'child_process';
import type { Stats } from 'fs';

export async function start(): Promise<void> {
  const appDirectories = appDirs({ appName: 'mango-tree-api-extractor' });
  const runtimeStats: Stats = await stat(process.execPath);
  const runtimeHash: string = createHash('md5')
    .update(`${runtimeStats.size}-${runtimeStats.mtimeMs}`)
    .digest('hex')
    .slice(0, 8);
  const cacheHashFilePath: string = join(appDirectories.data, '.cache-hash');
  const currentHash: string | null = existsSync(cacheHashFilePath) ? (await readFile(cacheHashFilePath)).toString() : null;
  const bundlePath: string = join(__dirname, '..', 'bundle');

  if (runtimeHash !== currentHash) {
    if (!existsSync(appDirectories.data)) await mkdir(appDirectories.data);

    const writeOperations: Array<PromiseSettledResult<void>> = await Promise.allSettled([
      writeFile(cacheHashFilePath, runtimeHash, { encoding: 'utf-8' }),
      copyDir(join(bundlePath, '.output'), join(appDirectories.data, '.output')),
      copyDir(join(bundlePath, '.nitro'), join(appDirectories.data, '.nitro')),
      copyDir(join(bundlePath, 'dist'), join(appDirectories.data, 'dist')),
    ]);

    for (const operation of writeOperations) {
      if (operation.status === 'rejected') throw Error(operation.reason);
    }
  }

  let backendPath: string = '';

  if (process.platform === 'darwin') backendPath = '/Applications/mango-tree-extractor/mango-tree-api-extractor-backend';
  if (
    process.platform === 'linux' ||
    process.platform === 'netbsd' ||
    process.platform === 'freebsd' ||
    process.platform === 'openbsd'
  ) backendPath = '/usr/local/bin/mango-tree-api-extractor-backend';
  if (process.platform === 'win32') backendPath = join(process.env.ProgramFiles as string, 'mango-tree-extractor', 'mango-tree-api-extractor-backend.exe');
  if (backendPath.length === 0) throw Error('unsupported platform...');

  const nitroHost = '127.0.0.1';
  const nitroPort = '3000';

  console.log(chalk.cyan(
    `🥭 Starting: frontend bind=${nitroHost}:${nitroPort} (IPv4) | backend=${backendPath} (expects 127.0.0.1:8000). ` +
    `Open the app at http://${nitroHost}:${nitroPort} to match the server bind exactly.`
  ));

  const backendProcess: ChildProcess = spawn(backendPath, {stdio: 'inherit'});
  const frontendProcess: ChildProcess = spawn(process.execPath, [join(appDirectories.data, '.output', 'server', 'index.mjs')], {
    env: { ...process.env, NITRO_HOST: nitroHost, NITRO_PORT: nitroPort },
  });

  backendProcess.on('error', (err) => {
    console.error(chalk.red(`Failed to start backend at ${backendPath}:`), err);
    process.exit(1);
  });

  backendProcess.on('exit', (code, signal) => {
    if (code !== 0 && code !== null) {
      console.error(chalk.red(`Backend exited with code ${code} (signal ${signal})`));
      process.exit(1);
    }
  });

  const handleKill = (): void => {
    console.log(chalk.bold.white('\n🥭 Shutting down API extractor...\n'));
    frontendProcess.kill();
    backendProcess.kill();
    process.exit();
  };

  process.on('SIGINT', handleKill);
  process.on('SIGTERM', handleKill)
}
