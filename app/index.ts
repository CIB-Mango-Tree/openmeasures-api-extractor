import { start } from '@/start';
import { drawScreen } from '@/screen';

async function main(): Promise<void> {
  await start();
  drawScreen();
}

main();
