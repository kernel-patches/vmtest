#!/bin/bash

travis_fold(){
  echo -ne "travis_fold:start:$1\\r"
}
travis_unfold(){
  echo -ne "travis_fold:end:$1\\r"
}
set -eux

travis_fold "Vmtest KERNEL: $KERNEL"
VMTEST_SETUPCMD="PROJECT_NAME=${PROJECT_NAME} ./${PROJECT_NAME}/travis-ci/vmtest/run_selftests.sh"

echo "KERNEL: $KERNEL"

travis_fold "Build latest pahole"
${VMTEST_ROOT}/build_pahole.sh travis-ci/vmtest/pahole
travis_unfold "Build latest pahole"

# Install required packagesi
travis_fold "Install latest clang"
wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | sudo apt-key add -
echo "deb http://apt.llvm.org/bionic/ llvm-toolchain-bionic main" | sudo tee -a /etc/apt/sources.list
sudo apt-get update
sudo apt-get -y install clang-12 lld-12 llvm-12
travis_unfold "Install latest clang"


# Build selftests (and latest kernel, if necessary)
travis_fold "Build kernel and selftests"
KERNEL="${KERNEL}" ${VMTEST_ROOT}/prepare_selftests.sh
travis_unfold "Build kernel and selftests"



travis_fold "Run selftests in VM"
# Escape whitespace characters.
setup_cmd=$(sed 's/\([[:space:]]\)/\\\1/g' <<< "${VMTEST_SETUPCMD}")
sudo adduser "${USER}" kvm

travis_fold "Run selftests in VM"
if [[ "${KERNEL}" = 'LATEST' ]]; then
  sudo -E sudo -E -u "${USER}" "${VMTEST_ROOT}/run.sh" -b "${REPO_ROOT}"  -o -d ~ -s "${setup_cmd}" ~/root.img;
else
  sudo -E sudo -E -u "${USER}" "${VMTEST_ROOT}/run.sh" -k "${KERNEL}*" -o -d ~ -s "${setup_cmd}" ~/root.img;
fi
travis_unfold "Run selftests in VM"

travis_unfold "Vmtest KERNEL: $KERNEL"

