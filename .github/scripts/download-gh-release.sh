#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$(dirname "$(realpath "$0")")

GH_REPO=$1
INSTALL_DIR=$(realpath $2)
# Optional: select the most recent release whose tag starts with this prefix,
# e.g. "gcc-16-" to track the latest GCC 16 build. A full tag also works, since
# a tag is a prefix of itself. When empty, use the most recent release overall.
TAG_PREFIX="${3:-}"

cd /tmp

bash "$SCRIPT_DIR/install-github-cli.sh"

tag=""
if [[ -n "$TAG_PREFIX" ]]; then
    # Releases are listed newest first, so the first match is the latest one.
    # The prefix is compared literally: quoting it on the right hand side of ==
    # keeps glob characters inert, so the dots in a tag cannot match anything
    # other than themselves.
    while IFS= read -r candidate; do
        if [[ "$candidate" == "$TAG_PREFIX"* ]]; then
            tag="$candidate"
            break
        fi
    done < <(gh release list -L 100 -R "${GH_REPO}" --json tagName -q '.[].tagName')
else
    tag=$(gh release list -L 1 -R ${GH_REPO} --json tagName -q .[].tagName)
fi
if [[ -z "$tag" ]]; then
    echo "Could not find a release${TAG_PREFIX:+ matching '${TAG_PREFIX}*'} at ${GH_REPO}"
    exit 1
fi
echo "Selected release tag: ${tag}"

url="https://github.com/${GH_REPO}/releases/download/${tag}/${tag}.tar.zst"
echo "Downloading $url"
wget -q "$url"

tarball=${tag}.tar.zst
dir=$(tar tf $tarball | head -1 || true)

echo "Extracting $tarball ..."
tar -I zstd -xf $tarball && rm -f $tarball

rm -rf $INSTALL_DIR
mv -v $dir $INSTALL_DIR

cd -
