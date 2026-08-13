import { start } from '@/start';
import { drawScreen } from '@/screen';
import type { StartResult } from '@/start';

async function main(): Promise<void> {
  const result: StartResult = await start();

  drawScreen(result);
}

main();
