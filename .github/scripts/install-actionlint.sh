#!/usr/bin/env bash
# Install only into this checkout; hashes are from the upstream v1.7.11 release.
set -euo pipefail

version=1.7.11
case "$(uname -s)-$(uname -m)" in
  Darwin-arm64)
    platform=darwin_arm64
    expected=a21ba7366d8329e7223faee0ed69eb13da27fe8acabb356bb7eb0b7f1e1cb6d8
    ;;
  Darwin-x86_64)
    platform=darwin_amd64
    expected=17ffc17fed8f0258ef6ad4aed932d3272464c7ef7d64e1cb0d65aa97c9752107
    ;;
  Linux-x86_64)
    platform=linux_amd64
    expected=900919a84f2229bac68ca9cd4103ea297abc35e9689ebb842c6e34a3d1b01b0a
    ;;
  Linux-aarch64 | Linux-arm64)
    platform=linux_arm64
    expected=21bc0dfb57a913fe175298c2a9e906ee630f747cb66d0a934d0d4b69f4ee1235
    ;;
  *)
    printf 'Unsupported platform. See the actionlint installation documentation.\n' >&2
    exit 1
    ;;
esac

mkdir -p .tools
archive="$(mktemp .tools/actionlint.XXXXXX)"
trap 'rm -f "$archive"' EXIT
curl --fail --location --silent --show-error --retry 3 \
  --output "$archive" \
  "https://github.com/rhysd/actionlint/releases/download/v${version}/actionlint_${version}_${platform}.tar.gz"

if command -v sha256sum >/dev/null 2>&1; then
  actual="$(sha256sum "$archive")"
else
  actual="$(shasum -a 256 "$archive")"
fi
if [[ "${actual%% *}" != "$expected" ]]; then
  printf 'actionlint archive checksum mismatch.\n' >&2
  exit 1
fi

tar -xzf "$archive" -C .tools actionlint
.tools/actionlint -version
