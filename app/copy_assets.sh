#!/bin/bash
set -euo pipefail

# Clear before copying: `cp -r` merges into an existing directory, so without this a rebuild
# leaves stale server chunks from a previous build behind and pkg snapshots the mixture.
mkdir -p bundle
rm -rf bundle/.output bundle/.nitro bundle/.tanstack bundle/dist

# Only these three exist: a clean `pnpm build` does not produce .tanstack (it is a leftover from
# older tooling), so copying it would fail on a fresh checkout.
cp -r ../site/.output ../site/.nitro ../site/dist bundle
