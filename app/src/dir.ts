import { mkdir, readdir, readFile, writeFile } from 'fs/promises';
import { join } from 'path';
import type { Dirent } from 'fs';

export async function copyDir(src: string, dest: string): Promise<void> {
  await mkdir(dest, { recursive: true });

  const entries: Array<Dirent> = await readdir(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = join(src, entry.name);
    const destPath = join(dest, entry.name);

    if (!entry.isDirectory()) {
      const content = await readFile(srcPath);

      await writeFile(destPath, content);
      continue;
    }

    await copyDir(srcPath, destPath);
  }
}
