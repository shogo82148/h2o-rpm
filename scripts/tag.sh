#!/bin/bash

set -eux

git switch main
git pull origin main

ROOT=$(git rev-parse --show-toplevel)
VERSION=$(perl -ne 'if (/^Version\s*:\s*([0-9.]+)$/) { print $1 }' "$ROOT/rpmbuild/SPECS/h2o.spec")
RELEASE=$(perl -ne 'if (/^Release\s*:\s*([0-9.]+)/) { print $1 }' "$ROOT/rpmbuild/SPECS/h2o.spec")

git tag -a -s -m "Release v$VERSION-$RELEASE" "v$VERSION-$RELEASE"
git push origin "v$VERSION-$RELEASE"
