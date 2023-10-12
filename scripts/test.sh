#!/bin/bash

set -exu

H2O_DISTRO=$1
IMAGE=$(perl -ne 'print $1 if /FROM\s+(.*)/' "Dockerfile.$H2O_DISTRO")
ROOT=$(cd "$(dirname "$0")/../" && pwd)
: "${PLATFORM:=linux/amd64}"

if [[ "$H2O_DISTRO" = amazonlinux2023 ]]; then
    docker run \
        --rm \
        -v "$ROOT/$H2O_DISTRO.build:/build" \
        --platform "$PLATFORM" \
        "$IMAGE" \
        sh -c "dnf update -y && dnf install -y \"/build/RPMS/\$(uname -m)/\"*.rpm"

elif [[ "$H2O_DISTRO" = amazonlinux2022 ]]; then
    docker run \
        --rm \
        -v "$ROOT/$H2O_DISTRO.build:/build" \
        --platform "$PLATFORM" \
        "$IMAGE" \
        sh -c "dnf update -y && dnf install -y \"/build/RPMS/\$(uname -m)/\"*.rpm"

elif docker run --rm --platform "$PLATFORM" "$IMAGE" sh -c "command -v dnf"; then
    if docker run --rm --platform "$PLATFORM" "$IMAGE" sh -c " dnf repolist --all" | grep powertools; then
        docker run \
            --rm \
            -v "$ROOT/$H2O_DISTRO.build:/build" \
            --platform "$PLATFORM" \
            "$IMAGE" \
            sh -c "dnf update -y && dnf --enablerepo powertools install -y \"/build/RPMS/\$(uname -m)/\"*.rpm"
    else
        docker run \
            --rm \
            -v "$ROOT/$H2O_DISTRO.build:/build" \
            --platform "$PLATFORM" \
            "$IMAGE" \
            sh -c "dnf update -y && dnf --enablerepo crb install -y \"/build/RPMS/\$(uname -m)/\"*.rpm"
    fi
else 
    docker run \
        --rm \
        -v "$ROOT/$H2O_DISTRO.build:/build" \
        --platform "$PLATFORM" \
        "$IMAGE" \
        sh -c "yum update -y; yum install -y epel-release; yum install -y \"/build/RPMS/\$(uname -m)/\"*.rpm"
fi
