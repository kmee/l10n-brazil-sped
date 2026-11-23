#!/bin/bash
# usage: tools/pva/gerar.sh OUT_DIR [KINDS]
# Generates the files of the scenarios, inside the oca-ci image of the series
# (with the PostgreSQL of the CI): copies cenarios/test_zz_pva.py into the
# tests of l10n_br_sped_efd_icms_ipi of THIS checkout (throwaway, never
# committed), installs the modules in a new database and runs only the tests
# of the scenarios, which write <kind>__<scenario>.txt in OUT_DIR. KINDS is a
# comma separated list of efd_icms_ipi, efd_pis_cofins, ecd and ecf (all by
# default). Fails when a test fails or a file is missing.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../.." && pwd)
mkdir -p "$1"
out=$(cd "$1" && pwd)
kinds=",${2:-efd_icms_ipi,efd_pis_cofins,ecd,ecf},"
cd "$repo"

mods=(l10n_br_sped_setup_tests)
tags=()
files=()
efd=l10n_br_sped_efd_icms_ipi
if [[ $kinds == *,efd_icms_ipi,* || $kinds == *,efd_pis_cofins,* ]]; then
    cp "$here/cenarios/test_zz_pva.py" "$efd/tests/test_zz_pva.py"
    grep -q "test_zz_pva" "$efd/tests/__init__.py" ||
        echo "from . import test_zz_pva" >>"$efd/tests/__init__.py"
    mods+=("$efd")
fi
if [[ $kinds == *,efd_icms_ipi,* ]]; then
    for class in TestPvaIcmsPresumido TestPvaIcmsPresumido0015 TestPvaIcmsPresumidoDevolucao; do
        tags+=("/$efd:$class")
    done
    files+=(efd_icms_ipi__presumido efd_icms_ipi__presumido_0015 efd_icms_ipi__presumido_devolucao)
fi
if [[ $kinds == *,efd_pis_cofins,* ]]; then
    mods+=(l10n_br_sped_efd_pis_cofins)
    tags+=("/$efd:TestPvaContribPresumido" "/$efd:TestPvaContribReal")
    files+=(efd_pis_cofins__presumido efd_pis_cofins__real_mes10 efd_pis_cofins__real_mes11)
fi
if [[ $kinds == *,ecd,* ]]; then
    mods+=(l10n_br_sped_ecd)
    tags+=("/l10n_br_sped_ecd:TestEcdCenario.test_termos_com_a_quantidade_de_linhas")
    files+=(ecd__presumido_2022)
    export ECD_GERAR_ARQUIVO="$out/ecd__presumido_2022.txt"
fi
if [[ $kinds == *,ecf,* ]]; then
    mods+=(l10n_br_sped_ecf)
    tags+=("/l10n_br_sped_ecf:TestEcfPresumido.test_gerar_arquivo_de_exemplo")
    files+=(ecf__presumido_2022)
    export ECF_GERAR_DEMO="$out/ecf__presumido_2022.txt"
fi
if [ ${#tags[@]} = 0 ]; then
    echo "gerar.sh: no known kind in '$kinds'" >&2
    exit 1
fi
INCLUDE=$(IFS=,; echo "${mods[*]}")
export INCLUDE PVA_SAIDA="$out"

git config --global --add safe.directory '*'
oca_install_addons
oca_wait_for_postgres
odoo -d pva_ci -i "$INCLUDE" --test-enable --test-tags "$(IFS=,; echo "${tags[*]}")" \
    --http-interface=127.0.0.1 --stop-after-init 2>&1 | tee "$out/geracao.log"

summary=$(grep -Eo "[0-9]+ failed, [0-9]+ error\(s\) of [0-9]+ tests" "$out/geracao.log" | tail -1 || true)
echo "gerar.sh: ${summary:-no test summary in the log}"
if [ "$summary" != "0 failed, 0 error(s) of ${#tags[@]} tests" ]; then
    echo "gerar.sh: expected 0 failed, 0 error(s) of ${#tags[@]} tests" >&2
    exit 1
fi
missing=0
for name in "${files[@]}"; do
    if [ ! -s "$out/$name.txt" ]; then
        echo "gerar.sh: $name.txt was not generated" >&2
        missing=1
    fi
done
exit $missing
