#!/bin/bash
# usage: tools/pva/confere.sh FILES_DIR
# Static check (confere.py) of the EFD files of FILES_DIR against the layout
# that sped-extractor extracted from the descriptor of the PVA. The layout is
# read from sped-extractor itself, pinned by commit, never copied here:
# - EFD ICMS/IPI, layout 20: akretion/sped-extractor#16 (contains #15);
# - EFD Contribuicoes, layout 6: akretion/sped-extractor#17 (#16 still has the
#   layout read from the PDF of the guide).
# The wheel of sped-extractor does not ship the CSVs of specs/, so they come
# from the source archive of the commit. Switch to the package from PyPI
# (and importlib.resources) when #15 to #17 are merged and released with the
# CSVs as package data.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
files=$1
repo=https://codeload.github.com/kmee/sped-extractor/tar.gz
icms_sha=67af03ad3cc47d0dcfb5e1c2c2432fc9cadb5929
pis_sha=89ed71e839bd4adf847fc4ce9bc1f8b57f69e312
cache=${PVA_CACHE:-${RUNNER_TEMP:-/tmp}/pva-ci-sped-extractor}

specs() {
    local sha=$1 layout=$2 dir="$cache/$1"
    if [ ! -d "$dir/spedextractor/specs/$layout" ]; then
        mkdir -p "$dir"
        curl -fsSL --retry 3 "$repo/$sha" | tar -xz -C "$dir" --strip-components=1
    fi
    echo "$dir/spedextractor/specs/$layout"
}

icms=$(specs "$icms_sha" efd_icms_ipi/20)
pis=$(specs "$pis_sha" efd_pis_cofins/6)
rc=0
shopt -s nullglob
for file in "$files"/efd_icms_ipi__*.txt; do
    python3 -I "$here/confere.py" icms "$file" --specs "$icms" || rc=1
done
for file in "$files"/efd_pis_cofins__*.txt; do
    python3 -I "$here/confere.py" pis "$file" --specs "$pis" || rc=1
done
exit $rc
