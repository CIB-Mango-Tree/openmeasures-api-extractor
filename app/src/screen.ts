import { join } from 'path';
import chalk from 'chalk';
import { BIG_LOGO, SMALL_LOGO, ASCII_TREE } from './ascii_art';
import type { StartResult } from './start';
import type { ChalkInstance } from 'chalk';

export function drawScreen(result: StartResult): void {
  const primaryColor: ChalkInstance = chalk.hex('#fcb103');

  if (process.stdout.columns >= 102) console.log(primaryColor(BIG_LOGO));
  if (process.stdout.columns < 102 && process.stdout.columns >= 78) console.log(primaryColor(SMALL_LOGO));
  if (process.stdout.columns < 78) console.log(primaryColor(`\nCIB Mango Tree\n`));

  console.log(primaryColor(ASCII_TREE));
  console.log(`${primaryColor.bold('CIB Mango Tree API Extractor')}\n     ${chalk.dim.white('For openmeasures')}\n`);
  console.log(`  ${primaryColor('→')} ${chalk.bold.white('API:')} ${result.apiUrl}`);
  console.log(`  ${primaryColor('→')} ${chalk.bold.white('UI:')}  ${chalk.underline(result.uiUrl)}`);
  console.log(`\n  ${chalk.dim.white('Open the UI link above in your browser. http://localhost:3000 works too.')}`);
  console.log(`\n  ${chalk.dim.white('Logs, if something goes wrong:')}`);
  console.log(`    ${chalk.dim.white(join(result.backendDataDir, 'diagnostics.log'))}`);
  console.log(`    ${chalk.dim.white(join(result.dataDir, 'diagnostics-frontend.log'))}`);
  console.log(`\n  ${chalk.dim.white('Press Ctrl+C to shut down.')}\n`);
}
