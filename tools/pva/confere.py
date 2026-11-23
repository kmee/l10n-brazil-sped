"""Static check of a SPED file against the layout extracted from the PVA.

usage: confere.py {icms|pis} FILE.txt --specs DIR [--resumo]

DIR is a layout directory of sped-extractor (spedextractor/specs/<kind>/<v>):
accurate_fields.csv, registers_pva.csv (or registers.csv) and values_pva.csv.
Checks the number of fields, required fields, size, type, valid values,
parent and child registers, required children, block counters (X990), 9900
and 9999, the CRLF line ends, and a few cross checks of the EFD ICMS/IPI that
the layout alone does not express (references to the 0150/0200/..., the
access key of the C100, the credit of the E110 against the C190). Exit code 1
when anything diverges. The PVA is still the judge: most refusals are
business rules this check does not see. Run it with python3 -I.
"""

import csv
import os
import re
import sys
from collections import Counter, OrderedDict, defaultdict

REFERENCES = {
    "COD_ITEM": "0200",
    "COD_PART": "0150",
    "UNID": "0190",
    "UNID_INV": "0190",
    "COD_NAT": "0400",
    "COD_OBS": "0460",
    "COD_CTA": "0500",
    "COD_INF": "0450",
}
KEY_FIELD = {
    "0200": "COD_ITEM",
    "0150": "COD_PART",
    "0190": "UNID",
    "0400": "COD_NAT",
    "0460": "COD_OBS",
    "0500": "COD_CTA",
    "0450": "COD_INF",
}


def read_csv(directory, *names):
    for name in names:
        path = os.path.join(directory, name + ".csv")
        if os.path.exists(path):
            with open(path, encoding="utf8") as handle:
                return list(csv.DictReader(handle))
    return []


def ymd(value):
    return value[4:] + value[2:4] + value[:2]


def key_digit(key):
    total = sum(int(d) * (2 + i % 8) for i, d in enumerate(reversed(key[:43])))
    digit = (11 - total % 11) % 11
    return str(digit if digit < 10 else 0)


def number(value):
    return float((value or "0").replace(",", "."))


class Checker:
    def __init__(self, kind, specs):
        self.kind = kind
        self.fields = defaultdict(list)
        for row in read_csv(specs, "accurate_fields"):
            self.fields[row["Register"]].append(row)
        if not self.fields:
            sys.exit(f"confere.py: no accurate_fields.csv in {specs}")
        for rows in self.fields.values():
            rows.sort(key=lambda row: int(row["Nº"]))
        self.values = {
            (row["register"], row["field"]): {
                value.split("=", 1)[0] for value in row["values"].split(";")
            }
            for row in read_csv(specs, "values_pva")
        }
        self.registers = OrderedDict(
            (row["code"], row) for row in read_csv(specs, "registers_pva", "registers")
        )
        self.levels = {
            code: int(row["level"])
            for code, row in self.registers.items()
            if row["level"].isdigit()
        }
        self.errors = []

    def error(self, line_no, register, field, message, content=""):
        self.errors.append((line_no, register, field, message, content[:100]))

    def record(self, line, register):
        values = line.split("|")[1:-1]
        return {
            field["Campo"]: (values[i] if i < len(values) else "")
            for i, field in enumerate(self.fields.get(register, []))
        }

    def check_field(self, line_no, register, values, i, field, line):
        value = values[i] if i < len(values) else ""
        name = field["Campo"]
        size = field["Tam"]
        fixed = size.endswith("*")
        size = int(size.rstrip("*")) if size.rstrip("*").isdigit() else None
        cancelled = (
            register == "C100"
            and len(values) > 5
            and values[5]
            in (
                "02",
                "03",
                "04",
                "05",
            )
        )
        if field["Obrig"] == "O" and value == "" and not (cancelled and i >= 3):
            self.error(line_no, register, name, "obrigatorio em branco", line)
            return
        if value == "":
            return
        if field["Tipo"] == "N":
            decimals = field["Dec"] if field["Dec"].isdigit() else ""
            if not re.fullmatch(r"-?\d+(,\d+)?", value):
                self.error(line_no, register, name, f"numero invalido '{value}'", line)
            else:
                whole, _sep, fraction = value.partition(",")
                whole = whole.lstrip("-")
                if decimals and len(fraction) > int(decimals):
                    self.error(
                        line_no,
                        register,
                        name,
                        f"mais de {decimals} casas decimais '{value}'",
                        line,
                    )
                if not decimals and fraction:
                    self.error(
                        line_no, register, name, f"inteiro com decimais '{value}'", line
                    )
                if size and fixed and len(whole) != size:
                    self.error(
                        line_no,
                        register,
                        name,
                        f"tamanho {len(value)}, esperado {size} (fixo)",
                        line,
                    )
                elif size and not fixed and len(whole) > size and not decimals:
                    self.error(
                        line_no, register, name, f"tamanho maior que {size}", line
                    )
        elif field["Tipo"] == "D":
            if not re.fullmatch(r"\d{8}", value):
                self.error(
                    line_no, register, name, f"data fora de DDMMAAAA '{value}'", line
                )
            elif not (1 <= int(value[:2]) <= 31 and 1 <= int(value[2:4]) <= 12):
                self.error(line_no, register, name, f"data invalida '{value}'", line)
        elif size and fixed and len(value) != size:
            self.error(
                line_no,
                register,
                name,
                f"tamanho {len(value)}, esperado {size} (fixo): '{value[:30]}'",
                line,
            )
        elif size and not fixed and len(value) > size:
            self.error(
                line_no,
                register,
                name,
                f"tamanho {len(value)} maior que {size}: '{value[:30]}'",
                line,
            )
        valid = self.values.get((register, name))
        if valid and value not in valid:
            self.error(
                line_no,
                register,
                name,
                f"valor '{value}' fora da lista {sorted(valid)[:8]}",
                line,
            )

    def check(self, raw):
        if b"\r\n" not in raw:
            self.error(0, "arquivo", "", "fim de linha nao e CRLF")
        text = raw.decode("latin-1")
        lines = [line for line in text.replace("\r", "").split("\n") if line.strip()]
        block_count = Counter()
        register_count = Counter()
        last_at_level = {}
        for line_no, line in enumerate(lines, 1):
            if not (line.startswith("|") and line.endswith("|")):
                self.error(line_no, "?", "", "linha sem pipe inicial e final", line)
                continue
            values = line.split("|")[1:-1]
            register = values[0]
            register_count[register] += 1
            block_count[register[0]] += 1
            layout = self.fields.get(register)
            if not layout:
                self.error(line_no, register, "", "registro fora do leiaute", line)
                continue
            if len(values) != len(layout):
                self.error(
                    line_no,
                    register,
                    "",
                    f"{len(values)} campos, o leiaute tem {len(layout)}",
                    line,
                )
            for i, field in enumerate(layout):
                self.check_field(line_no, register, values, i, field, line)
            level = self.levels.get(register)
            if level is None:
                continue
            if level > 0:
                parent = last_at_level.get(level - 1)
                if parent is None:
                    self.error(line_no, register, "", "registro filho sem pai", line)
            last_at_level[level] = line_no
            for deeper in [k for k in last_at_level if k > level]:
                del last_at_level[deeper]
        self.check_children(lines)
        self.check_counters(lines, block_count, register_count)
        if self.kind == "icms":
            self.check_icms(lines)
        return lines

    def check_children(self, lines):
        occurrences = defaultdict(list)
        for line_no, line in enumerate(lines, 1):
            occurrences[line.split("|")[1]].append(line_no)
        order = list(self.registers)
        for i, code in enumerate(order):
            level = self.levels.get(code)
            if code not in occurrences or level is None:
                continue
            j = i + 1
            while j < len(order) and self.levels.get(order[j], 99) > level:
                child = order[j]
                required = self.registers[child]["required"] == "True"
                if self.levels.get(child) == level + 1 and required:
                    if child not in occurrences:
                        line_no = occurrences[code][0]
                        self.error(
                            line_no,
                            code,
                            "",
                            f"filho obrigatorio {child} nao informado",
                            lines[line_no - 1],
                        )
                j += 1
        for code, row in self.registers.items():
            if (
                row["required"] == "True"
                and code not in occurrences
                and row["level"] in ("0", "1")
                and code[1:] != "990"
            ):
                self.error(0, code, "", "registro obrigatorio ausente")

    def check_counters(self, lines, block_count, register_count):
        for line_no, line in enumerate(lines, 1):
            values = line.split("|")
            register = values[1]
            if register.endswith("990") and len(values) > 2:
                if int(values[2]) != block_count[register[0]]:
                    self.error(
                        line_no,
                        register,
                        "QTD_LIN",
                        f"declara {values[2]}, o bloco tem {block_count[register[0]]}",
                    )
            if register == "9999" and int(values[2]) != len(lines):
                self.error(
                    line_no, "9999", "QTD_LIN", f"declara {values[2]}, tem {len(lines)}"
                )
            if register == "9900" and int(values[3]) != register_count[values[2]]:
                self.error(
                    line_no,
                    "9900",
                    values[2],
                    f"declara {values[3]}, existem {register_count[values[2]]}",
                )
        declared = {line.split("|")[2] for line in lines if line.startswith("|9900|")}
        for register in register_count:
            if register not in declared:
                self.error(0, "9900", register, f"falta o 9900 do {register}")

    def check_icms(self, lines):
        present = {line.split("|")[1] for line in lines}
        known = defaultdict(set)
        for line in lines:
            register = line.split("|")[1]
            if register in KEY_FIELD:
                known[register].add(
                    self.record(line, register).get(KEY_FIELD[register])
                )
        header = self.record(next(x for x in lines if x.startswith("|0000|")), "0000")
        start, end = header.get("DT_INI", ""), header.get("DT_FIN", "")
        credit = 0.0
        for line_no, line in enumerate(lines, 1):
            register = line.split("|")[1]
            if register not in self.fields:
                continue
            rec = self.record(line, register)
            for field, table in REFERENCES.items():
                value = rec.get(field)
                if value and table in present and register != table:
                    if value not in known[table]:
                        self.error(
                            line_no,
                            register,
                            field,
                            f"'{value[:20]}' nao existe no {table}",
                            line,
                        )
            if register == "C100":
                self.check_c100(line_no, line, rec, lines, start, end)
            if register == "C190" and rec.get("CFOP", "")[:1] in ("1", "2", "3"):
                credit += number(rec.get("VL_ICMS"))
        if "0100" not in present:
            self.error(0, "0100", "", "contador obrigatorio ausente")
        if header.get("IND_ATIV") == "0" and "E500" not in present:
            self.error(0, "E500", "", "IND_ATIV=0 (industrial) exige o E500")
        for line_no, line in enumerate(lines, 1):
            if line.startswith("|E110|"):
                value = number(self.record(line, "E110").get("VL_TOT_CREDITOS"))
                if abs(value - credit) > 0.005:
                    self.error(
                        line_no,
                        "E110",
                        "VL_TOT_CREDITOS",
                        f"{value:.2f} difere da soma do VL_ICMS dos C190"
                        f" de entrada ({credit:.2f})",
                        line,
                    )

    def check_c100(self, line_no, line, rec, lines, start, end):  # noqa: C901
        model, situation = rec.get("COD_MOD", ""), rec.get("COD_SIT", "")
        key = rec.get("CHV_NFE", "")
        if model in ("55", "65") and situation not in ("04", "05") and not key:
            self.error(
                line_no, "C100", "CHV_NFE", f"obrigatoria no modelo {model}", line
            )
        if key and not re.fullmatch(r"\d{44}", key):
            self.error(line_no, "C100", "CHV_NFE", "nao tem 44 digitos", line)
        elif key:
            if key_digit(key) != key[43]:
                self.error(
                    line_no, "C100", "CHV_NFE", "digito verificador errado", line
                )
            if model and key[20:22] != model:
                self.error(line_no, "C100", "CHV_NFE", "modelo difere do COD_MOD", line)
            if rec.get("NUM_DOC") and int(key[25:34]) != int(rec["NUM_DOC"]):
                self.error(line_no, "C100", "CHV_NFE", "numero difere do NUM_DOC", line)
            if (
                rec.get("IND_OPER") == "0"
                and rec.get("IND_EMIT") == "1"
                and rec.get("COD_PART")
            ):
                partner = next(
                    (
                        self.record(x, "0150")
                        for x in lines
                        if x.startswith("|0150|" + rec["COD_PART"] + "|")
                    ),
                    None,
                )
                if partner and partner.get("CNPJ") and partner["CNPJ"] != key[6:20]:
                    self.error(
                        line_no, "C100", "CHV_NFE", "CNPJ difere do participante", line
                    )
        issued, moved = rec.get("DT_DOC", ""), rec.get("DT_E_S", "")
        if issued and moved and ymd(moved) < ymd(issued):
            self.error(line_no, "C100", "DT_E_S", "entrada antes da emissao", line)
        if start and moved and situation in ("00", "01") and rec.get("IND_OPER") == "0":
            inside = ymd(start) <= ymd(moved) <= ymd(end)
            if situation == "01" and inside:
                self.error(line_no, "C100", "COD_SIT", "01 dentro do periodo", line)
            if situation == "00" and not inside:
                self.error(line_no, "C100", "COD_SIT", "00 fora do periodo", line)


def main(argv):
    kind, path = argv[1], argv[2]
    specs = argv[argv.index("--specs") + 1]
    checker = Checker(kind, specs)
    with open(path, "rb") as handle:
        lines = checker.check(handle.read())
    groups = OrderedDict()
    for line_no, register, field, message, content in checker.errors:
        key = (register, field, re.sub(r"'[^']*'", "'x'", re.sub(r"\d+", "N", message)))
        group = groups.setdefault(key, {"n": 0, "example": (line_no, message, content)})
        group["n"] += 1
    out = sys.stdout
    out.write(
        f"{path}: {len(lines)} linhas, {len(checker.errors)} divergencias "
        f"em {len(groups)} grupos\n"
    )
    for (register, field, _message), group in groups.items():
        line_no, message, content = group["example"]
        out.write(
            f"[{group['n']:3d}x] {register}.{field}: {message}  (linha {line_no})\n"
        )
        if "--resumo" not in argv and content:
            out.write(f"        {content}\n")
    return 1 if checker.errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
