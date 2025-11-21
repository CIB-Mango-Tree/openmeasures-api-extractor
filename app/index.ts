import { start } from '@/start';
import { DrawScreen } from '@/screen';

async function main(): Promise<void> {
  await start();
  DrawScreen();
}

main();
