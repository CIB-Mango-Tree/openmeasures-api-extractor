import chalk from 'chalk';
import { BIG_LOGO, SMALL_LOGO, ASCII_TREE } from './ascii_art';
import type { ChalkInstance } from 'chalk';

export function drawScreen(): void {
  const primaryColor: ChalkInstance = chalk.hex('#fcb103');

  if (process.stdout.columns >= 102) console.log(primaryColor(BIG_LOGO));
  if (process.stdout.columns < 102 && process.stdout.columns >= 78) console.log(primaryColor(SMALL_LOGO));
  if (process.stdout.columns < 78) console.log(primaryColor(`\nCIB Mango Tree\n`));

  console.log(primaryColor(ASCII_TREE));
  console.log(`${primaryColor.bold('CIB Mango Tree API Extractor')}\n     ${chalk.dim.white('For openmeasures')}\n`);
  console.log(`  ${primaryColor('\u2192')} ${chalk.bold.white('API:')} http://localhost:8000/api`);
  console.log(`  ${primaryColor('\u2192')} ${chalk.bold.white('UI:')} http://localhost:3000`);
}
