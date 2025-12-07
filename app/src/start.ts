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
  if (process.platform === 'win32') backendPath = join(process.env.LOCALAPPDATA as string, 'mango-tree-extractor', 'mango-tree-api-extractor-backend.exe');
  if (backendPath.length === 0) throw Error('unsupported platform...');

  const backendProcess: ChildProcess = spawn(backendPath);
  const frontendProcess: ChildProcess = spawn(process.execPath, [join(appDirectories.data, '.output', 'server', 'index.mjs')]);
  const handleKill = (): void => {
    console.log(chalk.bold.white('\n🥭 Shutting down API extractor...\n'));
    frontendProcess.kill();
    backendProcess.kill();
    process.exit();
  };

  process.on('SIGINT', handleKill);
  process.on('SIGTERM', handleKill)
}
