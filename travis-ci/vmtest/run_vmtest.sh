#!/bin/bash

travis_fold(){
  echo -ne "travis_fold:start:$1\\r"
}
travis_unfold(){
  echo -ne "travis_fold:end:$1\\r"
}
travis_fold "Vmtest_KERNEL_$KERNEL"
set -eux

VMTEST_SETUPCMD="PROJECT_NAME=${PROJECT_NAME} ./${PROJECT_NAME}/travis-ci/vmtest/run_selftests.sh"

echo "KERNEL: $KERNEL"

travis_fold "Build_latest_pahole"
${VMTEST_ROOT}/build_pahole.sh travis-ci/vmtest/pahole
travis_unfold "Build_latest_pahole"

# Install required packagesi
travis_fold "Install_latest_clang"
wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | sudo apt-key add -
echo "deb http://apt.llvm.org/bionic/ llvm-toolchain-bionic main" | sudo tee -a /etc/apt/sources.list
sudo apt-get update
sudo apt-get -y install clang-12 lld-12 llvm-12
travis_unfold "Install_latest_clang"


# Build selftests (and latest kernel, if necessary)
travis_fold "Build_kernel_and_selftests"
KERNEL="${KERNEL}" ${VMTEST_ROOT}/prepare_selftests.sh
travis_unfold "Build_kernel_and_selftests"



travis_fold "Run_selftests_in_VM"
# Escape whitespace characters.
setup_cmd=$(sed 's/\([[:space:]]\)/\\\1/g' <<< "${VMTEST_SETUPCMD}")
sudo adduser "${USER}" kvm

if [[ "${KERNEL}" = 'LATEST' ]]; then
  sudo -E sudo -E -u "${USER}" "${VMTEST_ROOT}/run.sh" -b "${REPO_ROOT}"  -o -d ~ -s "${setup_cmd}" ~/root.img;
else
  sudo -E sudo -E -u "${USER}" "${VMTEST_ROOT}/run.sh" -k "${KERNEL}*" -o -d ~ -s "${setup_cmd}" ~/root.img;
fi
travis_unfold "Run_selftests_in_VM"

travis_unfold "Vmtest_KERNEL_$KERNEL"

