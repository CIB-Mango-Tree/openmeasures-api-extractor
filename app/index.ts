import sea from 'node:sea';

function main(): void {
  console.log(`is SEA: ${sea.isSea()}`);
  console.log('sea object keys:', Object.keys(sea));
  console.log('sea.getAssetKeys type:', typeof sea.getAssetKeys);

  if (sea.isSea()) {
    const keys = sea.getAssetKeys();
    console.log(`executable assets: ${keys.length} assets loaded`);
  }
}

main();
