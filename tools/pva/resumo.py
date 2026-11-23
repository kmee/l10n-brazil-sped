"""Sum up the reports of the PVA and judge them against esperados.csv.

usage: resumo.py OUT_DIR FILES_DIR [--esperados esperados.csv]

Reads the <file>.json that pva_driver.py writes for every file and the text of
its reports (<file>_validacao.txt and, in the ECF, <file>_importacao.txt):
the summary of a report lists each message with its count under "Total de
Erros" and "Total de Advertencias" (or "Avisos"). Prints a Markdown summary
(also appended to $GITHUB_STEP_SUMMARY) and exits 1 when a file was not
validated, when the automation failed, or when a message is not in the
expected list. An expected message that did not show up is only a notice.
Run it with python3 -I.
"""

import csv
import fnmatch
import glob
import json
import os
import re
import sys

TOTAL = re.compile(r"^\s*Total de (Erros|Advert\S+|Avisos)\s+(\d+)\s*$")
LINE = re.compile(r"^\s*(\S.*?)\s{2,}(\d+)\s*$")


def normalize(text):
    return re.sub(r"\s+", " ", text).strip().rstrip(".")


def messages(path):
    """[(kind, message, count)] from the summary of a report."""
    found = []
    kind = None
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            match = TOTAL.match(line)
            if match:
                kind = "erro" if match.group(1) == "Erros" else "advertencia"
                continue
            if kind is None:
                continue
            if not line.strip():
                kind = None
                continue
            match = LINE.match(line)
            if match:
                found.append((kind, normalize(match.group(1)), int(match.group(2))))
    return found


def load_expected(path):
    with open(path, encoding="utf-8") as handle:
        return [
            {**row, "mensagem": normalize(row["mensagem"])}
            for row in csv.DictReader(handle)
            if row["escrituracao"] and not row["escrituracao"].startswith("#")
        ]


def covered(expected, kind, name, step, level, message):
    for row in expected:
        if (
            row["escrituracao"] == kind
            and fnmatch.fnmatch(name, row["arquivo"])
            and row["etapa"] == step
            and row["tipo"] == level
            and (
                message.startswith(row["mensagem"])
                or row["mensagem"].startswith(message)
            )
        ):
            return row
    return None


def main(argv):
    out, files = argv[1], argv[2]
    here = os.path.dirname(os.path.abspath(__file__))
    expected_path = (
        argv[argv.index("--esperados") + 1]
        if "--esperados" in argv
        else os.path.join(here, "esperados.csv")
    )
    expected = load_expected(expected_path)
    lines = ["## PVA", ""]
    failed = False
    used = set()
    names = sorted(
        os.path.basename(path)[:-4]
        for path in glob.glob(os.path.join(files, "*__*.txt"))
    )
    if not names:
        lines.append("Nenhum arquivo gerado para validar.")
        failed = True
    lines += [
        "| Arquivo | Resultado do PVA | Etapa | Tipo | Mensagem | Qtd | Situacao |",
        "|---|---|---|---|---|---|---|",
    ]
    notes = []
    for name in names:
        kind = name.split("__", 1)[0]
        json_path = os.path.join(out, name + ".json")
        if not os.path.exists(json_path):
            lines.append(f"| {name} | nao validado | | | | | FALHA |")
            failed = True
            continue
        with open(json_path, encoding="utf-8") as handle:
            data = json.load(handle)
        result = data.get("resultado") or "-"
        seconds = data.get("segundos")
        if data.get("situacao") != "ok":
            lines.append(
                f"| {name} | automacao falhou: {data.get('erro_da_automacao')}"
                " | | | | | FALHA |"
            )
            failed = True
            continue
        if result == "recusado_na_importacao":
            lines.append(f"| {name} | recusado na importacao | | | | | FALHA |")
            failed = True
            continue
        found = []
        for report in data.get("relatorios", []):
            step = "importacao" if report.endswith("_importacao.txt") else "validacao"
            for level, message, count in messages(os.path.join(out, report)):
                found.append((step, level, message, count))
        if result != "sucesso" and not found:
            lines.append(
                f"| {name} | {result}, sem relatorio legivel | | | | | FALHA |"
            )
            failed = True
            continue
        if not found:
            lines.append(
                f"| {name} | {result} ({seconds} s) | | | sem pendencias | | ok |"
            )
        for step, level, message, count in found:
            row = covered(expected, kind, name, step, level, message)
            if row:
                used.add(id(row))
                status = "esperado"
            else:
                status = "FALHA"
                failed = True
            lines.append(
                f"| {name} | {result} ({seconds} s) | {step} | {level} | {message}"
                f" | {count} | {status} |"
            )
    for row in expected:
        kinds_run = {name.split("__", 1)[0] for name in names}
        if id(row) not in used and row["escrituracao"] in kinds_run:
            notes.append(
                f"- esperado e nao apareceu: {row['escrituracao']} {row['etapa']} "
                f"{row['tipo']}: {row['mensagem']}"
            )
    if notes:
        lines += ["", "Avisos:", *notes]
    lines += ["", "Resultado: " + ("FALHA" if failed else "ok"), ""]
    text = "\n".join(lines)
    sys.stdout.write(text + "\n")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(text + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
