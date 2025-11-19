import { statSync, writeFileSync } from 'fs';
import { relative, } from 'path';
import { Command } from 'commander';
import { globSync } from 'glob';
import type { Stats } from 'fs';

type ExecArgvExtension = 'env' | 'cli' | 'none';
type SEAAssetMap = { [index: string]: string; };

type SEAConfig = {
  main: string;
  output: string;
  disableExperimentalSEAWarning: boolean;
  useSnapshot: boolean;
  useCodeCache: boolean;
  execArgv: Array<string>;
  execArgvExtension: ExecArgvExtension;
  assets: SEAAssetMap
};

type CLIParseOptions = {
  m: string;
  o: string;
  s: boolean;
  c: boolean;
  e: Array<string>;
  a: ExecArgvExtension;
  i: Array<string>;
  f: string;
};

function main(): void {
  const program = new Command();

  program
    .name('mango-tree-sea-config-builder')
    .description('CLI tool for creating a Node.JS Single Executable Application config for the mango-tree-api-extractor app')
    .version("1.0.0");
  program
    .option('-m', 'define name/path of main file', './build/index.mjs')
    .option('-o', 'define name/path of the Single Executable Application blob', './build/sea-blob.blob')
    .option('-s', 'enable snapshots', false)
    .option('-c', 'enable code caching', false)
    .option('-e [string...]', 'define execArgv options', ['--no-warnings', '--max-old-space-size=4096'])
    .option('-a', 'define argv extension', 'env')
    .option('-i [string...]', 'include asset files and directories', [])
    .option('-f [string]', 'define filepath of Single Executable Application Config', './sea-config.json');
  program.parse();

  const options = program.opts<CLIParseOptions>();
  let config: SEAConfig = {
    disableExperimentalSEAWarning: true,
    main: options.m,
    output: options.o,
    useSnapshot: options.s,
    useCodeCache: options.c,
    execArgv: options.e,
    execArgvExtension: options.a,
    assets: {}
  };

  if (options.i.length > 0) {
    config.assets = options.i.reduce<SEAAssetMap>((accumValue: SEAAssetMap, value: string): SEAAssetMap => {
      if (value.includes(':')) {
        const assetPair: Array<string> = value.split(':');

        if (assetPair.length === 1) throw Error(`asset pair is malformed: ${value}`);

        try {
          const key = assetPair[0] as string;
          const filePath = assetPair[1] as string;
          const fileStats: Stats = statSync(filePath);


          if (!fileStats.isFile()) throw Error(`file path in asset pair is not a file`);

          accumValue[key] = filePath;

          return accumValue;

        } catch (err: any) {
          if (err.code != null && err.code === 'ENOENT') throw Error('file path in asset pair does not exist');

          throw err;
        }
      }

      try {
        const fileStats: Stats = statSync(value);

        if (fileStats.isDirectory()) {
          const pattern: string = `${value}/**/*`;
          const glob: Array<string> = globSync(pattern, {
            nodir: true,
            dot: true,
            absolute: false,
            ignore: [
              '**/node_modules/**',
              `${value}/**/node_modules/**`
            ]
          });

          for (const file of glob) {
            const key: string = relative(process.cwd(), file)
              .replace(/\\/g, '/')
              .replace(/^\.\.\//, '');
            accumValue[key] = file;
          }

          return accumValue;
        }

      } catch (err: any) {
        throw err;
      }

      const ignoreRules: Array<string> = ['**/node_modules/**'];

      if (value.includes('/')) ignoreRules.push(
        `${value.split('/*')[0]}/**/node_modules/**`
      );

      const glob = globSync(value, {
        nodir: true,
        dot: true,
        absolute: false,
        ignore: ignoreRules
      });

      for (const file of glob) {
        const key: string = relative(process.cwd(), file)
          .replace(/\\/g, '/')
          .replace(/^\.\.\//, '');

        accumValue[key] = file;
      }

      return accumValue;
    }, {});
  }

  writeFileSync(options.f, JSON.stringify(config, null, 2), 'utf-8');
}

main();
