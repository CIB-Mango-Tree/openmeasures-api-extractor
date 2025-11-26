#!/bin/bash

mkdir -p bundle
cp ../api/dist/mango-tree-api-extractor-backend bundle
cp -r ../site/.output ../site/.nitro ../site/dist bundle
