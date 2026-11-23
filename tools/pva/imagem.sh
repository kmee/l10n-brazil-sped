#!/bin/bash
# usage: imagem.sh KIND
# Prints the tag of the local PVA image of KIND, building it first when it is
# missing: downloads the official installer listed in instaladores.csv, checks
# its SHA256 and builds the Dockerfile. The tag carries the version of the PVA
# and a hash of the Dockerfile, so a change in either builds a new image; the
# older images of the same kind are removed. Images are never pushed.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
kind=$1
line=$(awk -F, -v k="$kind" 'NR > 1 && $1 == k' "$here/instaladores.csv")
if [ -z "$line" ]; then
    echo "imagem.sh: $kind is not in instaladores.csv" >&2
    exit 1
fi
IFS=, read -r _ version url sha <<<"$line"
hash=$(cat "$here/Dockerfile" "$here/fix_arial.py" <(echo "$sha") | sha256sum | cut -c1-12)
repo="pva-ci-${kind//_/-}"
tag="$repo:$version-$hash"
# two runners share the Docker of the machine: one build per kind at a time
exec 9>"/tmp/pva-ci-imagem-$kind.lock"
flock 9
if ! docker image inspect "$tag" >/dev/null 2>&1; then
    work=$(mktemp -d "${RUNNER_TEMP:-/tmp}/pva-ci-build-XXXXXX")
    trap 'rm -rf "$work"' EXIT
    echo "imagem.sh: building $tag from $url" >&2
    curl -fsSL --retry 3 --retry-delay 10 -o "$work/instalador.sh" "$url"
    echo "$sha  $work/instalador.sh" | sha256sum -c - >&2
    cp "$here/Dockerfile" "$here/fix_arial.py" "$work/"
    DOCKER_BUILDKIT=1 docker build -t "$tag" "$work" >&2
    docker images "$repo" --format '{{.Repository}}:{{.Tag}}' | grep -vxF "$tag" |
        xargs -r docker rmi >&2 || true
fi
echo "$tag"
