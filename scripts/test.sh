#!/bin/bash

set -exu

H2O_DISTRO=$1
IMAGE=$(perl -ne 'print $1 if /FROM\s+(.*)/' "Dockerfile.$H2O_DISTRO")
ROOT=$(cd "$(dirname "$0")/../" && pwd)
: "${PLATFORM:=linux/amd64}"

docker run \
    --rm \
    -v "$ROOT/$H2O_DISTRO.build:/build" \
    --platform "$PLATFORM" \
    "$IMAGE" \
    sh -c "if command -v dnf; then dnf update -y && dnf --enablerepo powertools install -y \"/build/RPMS/\$(uname -m)/\"*.rpm; else yum update -y; yum install -y epel-release; yum install -y \"/build/RPMS/\$(uname -m)/\"*.rpm; fi"
