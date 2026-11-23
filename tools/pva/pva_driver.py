#!/usr/bin/env python3
"""Drive the PVA of the Receita Federal: import one SPED file, validate it and
save the reports as PDF and text.

usage: pva_driver.py KIND FILE OUTDIR NAME
  KIND    efd_icms_ipi | efd_pis_cofins | ecd | ecf
  FILE    the file to validate, inside the container
  OUTDIR  where the screens, the reports and NAME.json go

Runs inside the PVA image (see Dockerfile), as the user of the image: starts
Xvfb and the PVA itself. There is no window manager, so the keyboard only
reaches a window that took the focus by itself: the dialogs are answered by
Return or Escape when that works and by a click relative to the dialog
otherwise. Every step waits for a window by its title, never a fixed sleep.
Environment: PVA_DIR (default /opt/pva), PVA_ATUALIZAR_TABELAS=1 to accept the
update of the official tables (the container needs network for that).
Exit code: 0 when the PVA gave a result (the result itself is in NAME.json),
2 when the automation got lost (screens in OUTDIR).
"""

import json
import os
import re
import subprocess
import sys
import time

DISPLAY = ":99"
ENV = dict(os.environ, DISPLAY=DISPLAY)
PVA_DIR = os.environ.get("PVA_DIR", "/opt/pva")
UPDATE_TABLES = os.environ.get("PVA_ATUALIZAR_TABELAS") == "1"

# Screen positions are absolute on a 1280x1024 screen: the main window of
# each PVA always opens at the same place. Dialogs are handled by title and
# their own geometry.
KINDS = {
    "efd_icms_ipi": {
        "exe": "SpedEFD",
        "main": r"EFD ICMS/IPI",
        # menu Escrituracao Fiscal > Nova > Importar
        "open_import": [(303, 225), (283, 250), (576, 270)],
        "report": {
            "boxes": [(672, 393), (740, 393)],
            "show": (855, 393),
            "save": (529, 434),
        },
        # validated with no pending item: Relatorio de Pendencias in the tree
        "success_report": {"tree": (322, 460), "save": (529, 389)},
    },
    "efd_pis_cofins": {
        "exe": "SpedContribuicoes",
        "main": r"EFD Contribui",
        "open_import": [(307, 226), (285, 254), (619, 278)],
        "report": {
            "boxes": [(704, 396), (766, 396)],
            "show": (855, 396),
            "save": (529, 436),
        },
        # validated with no pending item the PVA has no report: the screen is
        # the evidence
        "success_report": None,
    },
    "ecd": {
        "exe": "SpedContabil",
        "main": r"^Sped Cont",
        "open_import": [(190, 185)],
        "report": {
            "boxes": [(677, 356), (745, 356)],
            "show": (872, 356),
            "save": (449, 400),
        },
        "split": 407,
        "success_report": None,
    },
    "ecf": {
        "exe": "SpedECF",
        "main": r"^Sped ECF",
        "open_import": [(175, 185)],
        "report": {
            "boxes": [(739, 356), (808, 356)],
            "show": (934, 356),
            "save": (572, 400),
        },
        "success_report": None,
        # after the import the ECF asks "Campos de transporte devem ser
        # atualizados automaticamente?" in a dialog wider than 1000 pixels
        # (answered Nao, so the validation judges the values written by
        # Odoo) and, when it rewrote lines, whether to show the import
        # report (answered Sim, to keep it). Then the file is opened from
        # the tree and validated by the Passo a Passo.
        "transport_question": True,
        "split": 528,
        "close_tab": (699, 224),
        "tree_item": (154, 299),
        "validate": (795, 575),
    },
}

# JOptionPane titles: answered with Return (the default button, Sim or Ok)
QUESTION = re.compile(r"^(Aviso|Mensagem|Erro|Confirma\w*|Aten\w*|Pergunta|Advert\w*)$")
WAIT = re.compile(
    r"^(Aguarde.*|Validando.*|Informativos.*|Importando.*|Processando.*|)$"
)
CHOOSER = re.compile(r"^Importar Escritura")
SAVE = re.compile(r"^(Save|Salvar)$")
TABLES = re.compile(r"^Atualizar Tabelas")
BLOCKS = re.compile(r"^Importa\S+ por blocos")
# "Validando assinaturas" shows up during the import: not the validation
VALIDATING = re.compile(r"^Validando a escritura")
# one pixel of "convert ... txt:-": "209,0: (220,143,63) #DC8F3F ..."
PIXEL = re.compile(r"(\d+),0:\s*\(\s*(\d+),\s*(\d+),\s*(\d+)")
RESULT = {"Mensagem": "sucesso", "Aviso": "advertencias", "Erro": "erros"}


class Lost(Exception):
    """The automation is on a screen it does not know."""


def run(*cmd, check=False):
    return subprocess.run(
        cmd, env=ENV, capture_output=True, text=True, check=check
    ).stdout


class Driver:
    def __init__(self, kind, path, outdir, name):
        self.kind = kind
        self.cfg = KINDS[kind]
        self.path = path
        self.outdir = outdir
        self.name = name
        self.screens = []
        self.reports = []
        self.step = 0
        self.start = time.time()
        self.main_id = None
        self.result = None
        self.result_title = None
        os.makedirs(outdir, exist_ok=True)

    # ---------------------------------------------------------------- X
    def log(self, msg):
        sys.stdout.write(f"[{time.time() - self.start:6.1f}s] {self.name}: {msg}\n")
        sys.stdout.flush()

    def windows(self):
        found = []
        for wid in run("xdotool", "search", "--onlyvisible", "--name", ".*").split():
            title = run("xdotool", "getwindowname", wid).strip()
            if title in ("Content window", "FocusProxy"):
                continue
            geo = dict(
                line.split("=", 1)
                for line in run("xdotool", "getwindowgeometry", "--shell", wid).split()
                if "=" in line
            )
            if not geo or int(geo.get("WIDTH", 0)) < 50:
                continue
            found.append(
                {
                    "id": wid,
                    "title": title,
                    "x": int(geo["X"]),
                    "y": int(geo["Y"]),
                    "w": int(geo["WIDTH"]),
                    "h": int(geo["HEIGHT"]),
                }
            )
        return found

    def dialogs(self):
        """Visible windows other than the main one and the root."""
        result = []
        for win in self.windows():
            if win["w"] >= 1280 and win["h"] >= 1024:
                continue
            if re.search(self.cfg["main"], win["title"]):
                self.main_id = win["id"]
                continue
            result.append(win)
        return result

    def has_main(self):
        return any(re.search(self.cfg["main"], w["title"]) for w in self.windows())

    def click(self, x, y, double=False):
        if double:
            run(
                "xdotool",
                "mousemove",
                str(x),
                str(y),
                "click",
                "--repeat",
                "2",
                "--delay",
                "120",
                "1",
            )
        else:
            run("xdotool", "mousemove", str(x), str(y), "click", "1")
        time.sleep(0.8)

    def key(self, name):
        run("xdotool", "key", name)
        time.sleep(0.8)

    def type(self, text):
        run("xdotool", "type", "--delay", "40", text)
        time.sleep(0.5)

    def shot(self, label):
        self.step += 1
        path = os.path.join(self.outdir, f"{self.name}_{self.step:02d}_{label}.png")
        run("import", "-window", "root", path)
        self.screens.append(os.path.basename(path))
        return path

    def split_x(self):
        """Column of the divider of the main window (its orange arrows).

        In the ECD and the ECF the right panel starts at a divider that moves
        a few pixels from one run to the other: the positions of the right
        panel are written for the divider at cfg["split"] and shifted here.
        """
        run("import", "-window", "root", "/tmp/pva-ci-linha.png")
        out = run(
            "convert",
            "/tmp/pva-ci-linha.png",
            "-crop",
            "400x1+300+300",
            "-depth",
            "8",
            "txt:-",
        )
        for line in out.splitlines()[1:]:
            match = PIXEL.match(line)
            if match:
                x, r, g, b = (int(v) for v in match.groups())
                if r > 180 and 60 < g < 150 and b < 90:
                    return 300 + x
        return None

    def at(self, point, centered=False):
        """Point of the right panel, shifted with its divider."""
        reference = self.cfg.get("split")
        if not reference:
            return point
        found = self.split_x()
        if found is None:
            return point
        delta = found - reference
        if centered:
            delta //= 2
        if delta:
            self.log(f"divider at {found}, shifting {delta}")
        return (point[0] + delta, point[1])

    def wait_for(self, pattern, timeout, what):
        limit = time.time() + timeout
        while time.time() < limit:
            for win in self.dialogs():
                if re.search(pattern, win["title"]):
                    return win
            time.sleep(1)
        self.shot(f"sem_{what}")
        raise Lost(f"no window {what!r} after {timeout}s: {self.dialogs()}")

    # ------------------------------------------------------------ steps
    def launch(self):
        subprocess.Popen(
            ["Xvfb", DISPLAY, "-screen", "0", "1280x1024x24"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(2)
        log = open(os.path.join(self.outdir, f"{self.name}_pva.log"), "w")
        subprocess.Popen(
            [os.path.join(PVA_DIR, self.cfg["exe"])],
            cwd=PVA_DIR,
            env=ENV,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        self.log(f"PVA {self.cfg['exe']} started")

    def tables(self, win):
        """Atualizar Tabelas: Escape cancels, Return accepts."""
        self.log(f"tables dialog, {'update' if UPDATE_TABLES else 'cancel'}")
        self.key("Return" if UPDATE_TABLES else "Escape")

    def wait_ready(self, timeout=420):
        """Main window up and idle: no dialog for 6 seconds."""
        limit = time.time() + timeout
        quiet_since = None
        seen = {}
        while time.time() < limit:
            dialogs = self.dialogs() if self.has_main() else [{"title": "(no main)"}]
            if not dialogs:
                quiet_since = quiet_since or time.time()
                if time.time() - quiet_since >= 6:
                    self.log("PVA ready")
                    return
            else:
                quiet_since = None
                for win in dialogs:
                    title = win["title"]
                    if TABLES.search(title):
                        self.tables(win)
                    elif QUESTION.match(title):
                        # e.g. "nao foi possivel verificar a versao" without network
                        self.log(f"{title} at start: Return")
                        self.shot(f"inicio_{win['w']}x{win['h']}")
                        self.key("Return")
                    elif title == "(no main)" or WAIT.match(title):
                        pass
                    else:
                        first = seen.setdefault(title, time.time())
                        if time.time() - first > 60:
                            self.shot("inicio_desconhecido")
                            raise Lost(f"unknown window at start: {title!r}")
            time.sleep(1)
        self.shot("inicio_timeout")
        raise Lost("the PVA did not get ready")

    def open_import(self):
        for attempt in range(3):
            for x, y in self.cfg["open_import"]:
                self.click(x, y)
            try:
                return self.wait_for(CHOOSER, 30, "seletor_de_arquivo")
            except Lost:
                self.log(f"no file chooser (attempt {attempt + 1}), retrying")
                self.key("Escape")
                self.wait_ready(120)
        raise Lost("the import menu never opened the file chooser")

    def focus_name_field(self, win):
        """Click the file name field of a file chooser (two look and feels)."""
        offset = {500: (296, 242), 530: (320, 229)}.get(win["w"])
        if offset:
            self.click(win["x"] + offset[0], win["y"] + offset[1])

    def choose_file(self, chooser, path):
        """Type the path in the name field and Return."""
        self.focus_name_field(chooser)
        self.type(path)
        self.key("Return")
        limit = time.time() + 20
        while time.time() < limit:
            if not any(w["id"] == chooser["id"] for w in self.dialogs()):
                return
            time.sleep(1)
        self.shot("seletor_preso")
        raise Lost(f"the file chooser did not take {path}")

    def handle(self, win, state):
        """Answer one dialog of the import or the validation.

        Returns True when the result of the validation (or a refusal of the
        import) was read.
        """
        title = win["title"]
        expect_result = state["validating"]
        if QUESTION.match(title) and (expect_result or title == "Erro"):
            self.result_title = title
            if expect_result:
                self.result = RESULT.get(title, "desconhecido")
            else:
                # an error before the validation is a refused import
                self.result = "recusado_na_importacao"
            self.log(f"result: {title} ({self.result})")
            self.shot("resultado")
            self.key("Return")
            return True
        if self.cfg.get("transport_question") and QUESTION.match(title):
            self.shot(f"pergunta_{win['w']}x{win['h']}")
            if win["w"] >= 1000:
                self.log("campos de transporte: Nao")
                self.click(win["x"] + win["w"] // 2 + 40, win["y"] + win["h"] - 27)
                state["answered"].add("transporte")
            else:
                self.log(f"{title} {win['w']}x{win['h']}: Return")
                self.key("Return")
                if "transporte" in state["answered"]:
                    state["answered"].add("linhas")
        elif QUESTION.match(title):
            self.log(f"{title} {win['w']}x{win['h']}: Return")
            self.shot(f"pergunta_{win['w']}x{win['h']}")
            self.key("Return")
        elif TABLES.search(title):
            self.tables(win)
            state["tables"] = True
        elif BLOCKS.search(title):
            self.log("import by blocks: Ok")
            self.click(win["x"] + 250, win["y"] + win["h"] - 56)
        elif not CHOOSER.search(title):
            first = state["unknown"].setdefault(title, time.time())
            if time.time() - first > 90:
                self.shot("janela_desconhecida")
                raise Lost(f"unknown window {title!r}")
        return False

    def ecf_step(self, state):
        """ECF: once the import is quiet, open the file and validate it."""
        state["quiet"] = state["quiet"] or time.time()
        wait = 10 if "transporte" in state["answered"] else 60
        if time.time() - state["quiet"] > wait and not state["validated"]:
            self.ecf_validate(state["answered"])
            state["validated"] = True
            state["quiet"] = None

    def import_and_validate(self, timeout=1800):
        """From the file chooser to the result of the validation."""
        chooser = self.open_import()
        self.choose_file(chooser, self.path)
        limit = time.time() + timeout
        state = {
            "validating": False,
            "validated": False,
            "tables": False,
            "answered": set(),
            "unknown": {},
            "quiet": None,
        }
        last = None
        while time.time() < limit:
            dialogs = [w for w in self.dialogs() if not WAIT.match(w["title"])]
            titles = sorted(w["title"] for w in self.dialogs())
            if titles != last:
                self.log(f"windows {titles}")
                last = titles
            if any(VALIDATING.search(t) for t in titles):
                state["validating"] = True
            for win in dialogs:
                if self.handle(win, state):
                    return
            if titles:
                state["quiet"] = None
            elif self.cfg.get("transport_question") and not state["validating"]:
                self.ecf_step(state)
            time.sleep(0.4)
        self.shot("validacao_timeout")
        raise Lost("no result from the validation")

    def ecf_validate(self, answered):
        if "linhas" in answered:
            self.save_report("importacao")
        self.click(*self.at(self.cfg["close_tab"]))
        time.sleep(2)
        self.click(*self.cfg["tree_item"], double=True)
        time.sleep(6)
        self.shot("passo_a_passo")
        # the icon only takes the click once the Passo a Passo is drawn:
        # click again until the PVA shows a window
        for attempt in range(6):
            self.log(f"Passo a Passo: Validar (attempt {attempt + 1})")
            self.click(*self.at(self.cfg["validate"]))
            limit = time.time() + 40
            while time.time() < limit:
                if self.dialogs():
                    return
                time.sleep(1)
        self.shot("validar_sem_resposta")
        raise Lost("the Validar icon of the ECF never answered")

    def save_report(self, label, cfg=None):
        """On a report screen: tick the boxes, show, save as PDF, to text."""
        cfg = cfg or self.cfg["report"]
        time.sleep(2)
        for point in cfg.get("boxes", []):
            self.click(*self.at(point, centered=True))
        if cfg.get("show"):
            self.click(*self.at(cfg["show"], centered=True))
            time.sleep(8)
        self.shot(f"relatorio_{label}")
        self.click(*self.at(cfg["save"]))
        try:
            dialog = self.wait_for(SAVE, 30, "salvar")
        except Lost:
            self.log(f"no save dialog for the {label} report")
            return None
        pdf = f"/tmp/pva-ci-{self.name}_{label}.pdf"
        self.focus_name_field(dialog)
        self.type(pdf)
        self.key("Return")
        limit = time.time() + 60
        size = -1
        while time.time() < limit:
            if os.path.exists(pdf) and os.path.getsize(pdf) == size and size > 0:
                break
            size = os.path.getsize(pdf) if os.path.exists(pdf) else -1
            time.sleep(2)
        if any(w["id"] == dialog["id"] for w in self.dialogs()):
            self.key("Escape")
        if not os.path.exists(pdf):
            self.shot(f"sem_pdf_{label}")
            self.log(f"the {label} report was not saved")
            return None
        target = os.path.join(self.outdir, f"{self.name}_{label}.pdf")
        os.replace(pdf, target)
        run("pdftotext", "-layout", target, target[:-4] + ".txt")
        self.reports.append(os.path.basename(target[:-4] + ".txt"))
        self.log(f"report {label} saved")
        return target

    def reports_after_result(self):
        time.sleep(3)
        # some PVAs repeat the result dialog over the report
        for win in self.dialogs():
            if QUESTION.match(win["title"]):
                self.key("Return")
        if self.result == "sucesso":
            success = self.cfg.get("success_report")
            if success:
                self.click(*success["tree"])
                time.sleep(5)
                for win in self.dialogs():
                    if QUESTION.match(win["title"]):
                        self.key("Return")
                self.save_report("validacao", {"save": success["save"]})
            else:
                time.sleep(3)
                self.shot("validado")
        else:
            self.save_report("validacao")

    def write_result(self, status, error=None):
        data = {
            "escrituracao": self.kind,
            "nome": self.name,
            "arquivo": os.path.basename(self.path),
            "situacao": status,
            "resultado": self.result,
            "titulo_do_resultado": self.result_title,
            "relatorios": self.reports,
            "telas": self.screens,
            "erro_da_automacao": error,
            "segundos": round(time.time() - self.start),
            "atualizou_tabelas": UPDATE_TABLES,
        }
        with open(os.path.join(self.outdir, f"{self.name}.json"), "w") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=1)

    def main(self):
        try:
            self.launch()
            self.wait_ready()
            self.shot("pronto")
            self.import_and_validate()
            self.reports_after_result()
            self.shot("fim")
        except Lost as error:
            self.log(f"LOST: {error}")
            self.write_result("automacao_falhou", str(error))
            return 2
        self.write_result("ok")
        self.log(f"done: {self.result}")
        return 0


if __name__ == "__main__":
    kind, path, outdir, name = sys.argv[1:5]
    sys.exit(Driver(kind, path, outdir, name).main())
