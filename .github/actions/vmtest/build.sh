#!/bin/bash

set -euo pipefail

THISDIR="$(cd $(dirname $0) && pwd)"

source "${THISDIR}"/helpers.sh

travis_fold start build_kernel "Building kernel"

cp "${GITHUB_ACTION_PATH}"/latest.config .config
make LLVM=1 \
  LD=lld-${LLVM_VER} HOSTLD=lld-${LLVM_VER} \
	CLANG=clang-${LLVM_VER} \
	LLC=llc-${LLVM_VER} \
	LLVM_STRIP=llvm-strip-${LLVM_VER} \
  LD=ld.lld-15 HOSTLD=ld.lld-15 \
  -j $((4*$(nproc))) olddefconfig all > /dev/null

travis_fold end build_kernel
