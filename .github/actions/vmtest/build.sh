#!/bin/bash

set -euo pipefail

THISDIR="$(cd $(dirname $0) && pwd)"

source "${THISDIR}"/helpers.sh

travis_fold start build_kernel "Building kernel"

cp "${GITHUB_ACTION_PATH}"/latest.config .config

LLVM_VER=15

make LLVM=1 \
  CC=clang-${LLVM_VER} HOSTCC=clang-${LLVM_VER}\
  LD=ld.lld-${LLVM_VER} HOSTLD=ld.lld-${LLVM_VER} \
  -j $((4*$(nproc))) olddefconfig all > /dev/null

travis_fold end build_kernel
