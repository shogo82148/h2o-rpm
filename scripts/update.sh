#!/bin/bash

CURRENT=$(cd "$(dirname "$0")" && pwd)
cd "$CURRENT"

set -euxp pipefail

export LC_ALL=en_US.UTF-8

H2O_VERSION=$(gh api --jq '.sha' /repos/h2o/h2o/commits/heads/master)
export H2O_VERSION

RELEASE=$(perl -nle 'print 1+$1 if /^Release: (\d+)%\{\?dist\}$/' "$CURRENT/../rpmbuild/SPECS/h2o.spec")
export RELEASE

RELAESE_DATE=$(perl -e 'use POSIX qw(strftime); print strftime("%a %b %d %Y\n", localtime);')
export RELAESE_DATE

perl -i -pe 's/SOURCE_ARCHIVE := [0-9a-fA-F]*.tar.gz/SOURCE_ARCHIVE := $ENV{H2O_VERSION}.tar.gz/' "$CURRENT/../Makefile"

perl -i -pe 's(Source0: https://github.com/h2o/h2o/archive/[0-9a-fA-F]*.tar.gz)(Source0: https://github.com/h2o/h2o/archive/$ENV{H2O_VERSION}.tar.gz)' "$CURRENT/../rpmbuild/SPECS/h2o.spec"
perl -i -pe 's/%setup -q -n h2o-[0-9a-fA-F]*/%setup -q -n h2o-$ENV{H2O_VERSION}/' "$CURRENT/../rpmbuild/SPECS/h2o.spec"

perl -i -pe 's/^Release: \d+%\{\?dist\}$/Release: $ENV{RELEASE}%{?dist}/' "$CURRENT/../rpmbuild/SPECS/h2o.spec"
perl -i -pe 's/^%changelog$/%changelog\n\n* $ENV{RELAESE_DATE} ICHINOSE Shogo <shogo82148\@gmail.com> - 2.3.0-$ENV{RELEASE}\n- bump v2.3.0-$ENV{H2O_VERSION}/' "$CURRENT/../rpmbuild/SPECS/h2o.spec"

if [[ -f "${GITHUB_OUTPUT:-}" ]]; then
    cat <<__END_OF_OUTPUT__ >> "$GITHUB_OUTPUT"
latest-version=$H2O_VERSION
__END_OF_OUTPUT__
fi
