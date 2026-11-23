#!/bin/bash
# usage: validar.sh FILES_DIR OUT_DIR
# Validates every <kind>__<scenario>.txt of FILES_DIR in the PVA of its kind:
# one container per file, named $PVA_PREFIXO-<file>, without network unless
# PVA_ATUALIZAR_TABELAS=1. The screens, the reports and one <file>.json per
# file go to OUT_DIR; resumo.py reads them. Exit code 1 when the automation
# failed on any file (the content of the reports is judged by resumo.py).
set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd)
files=$1
out=$2
prefix=${PVA_PREFIXO:-pva-ci-local}
update=${PVA_ATUALIZAR_TABELAS:-0}
mkdir -p "$out"
network=(--network none)
[ "$update" = 1 ] && network=()
rc=0
shopt -s nullglob
for file in "$files"/*__*.txt; do
    name=$(basename "$file" .txt)
    kind=${name%%__*}
    if ! tag=$("$here/imagem.sh" "$kind"); then
        echo "validar.sh: no image for $kind" >&2
        rc=1
        continue
    fi
    container="$prefix-$name"
    docker rm -f "$container" >/dev/null 2>&1
    echo "::group::PVA $name ($tag)"
    docker run -d --rm --name "$container" "${network[@]}" "$tag" sleep infinity >/dev/null
    docker cp "$here/pva_driver.py" "$container:/tmp/pva_driver.py"
    docker cp "$file" "$container:/tmp/$name.txt"
    timeout "${PVA_TIMEOUT:-2700}" docker exec -e PVA_ATUALIZAR_TABELAS="$update" \
        "$container" python3 /tmp/pva_driver.py "$kind" "/tmp/$name.txt" /tmp/pva-ci-saida "$name" |
        tee "$out/$name.driver.log"
    driver=${PIPESTATUS[0]}
    docker cp "$container:/tmp/pva-ci-saida/." "$out/" >/dev/null 2>&1
    docker rm -f "$container" >/dev/null 2>&1
    echo "::endgroup::"
    if [ "$driver" != 0 ]; then
        echo "validar.sh: the automation failed on $name (exit $driver)" >&2
        rc=1
    fi
done
exit $rc
