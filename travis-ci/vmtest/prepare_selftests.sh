#!/bin/bash

set -eux

cp ${VMTEST_ROOT}/configs/latest.config .config
make -j $((4*$(nproc))) olddefconfig all
