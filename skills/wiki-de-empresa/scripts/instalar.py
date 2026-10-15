# -*- coding: utf-8 -*-
"""Instala o pone al día la wiki corporativa en un repo que YA tiene el DAG estándar (dag-de-proyecto).

    python3 instalar.py <repo> --empresa NOMBRE [--enlaces enlaces.json]            # ensayo
    python3 instalar.py <repo> --empresa NOMBRE [--enlaces enlaces.json] --aplicar  # escribe

Hace, y nunca pisa lo que ya existe en docs/empresa/ (son de la empresa):
  1. plan/nodos_empresa.py  (VENDORIZADO: catálogo embebido, el repo sigue autónomo) + plan/enlaces_empresa.json (de la empresa)
  2. engancha `nodos_empresa.registrar(n)` en plan/construir_dag.py (una vez)
  3. siembra docs/empresa/ (arquitectura, un esqueleto por capítulo con secciones y marcador POR COMPLETAR, sistemas),
     analisis/ (exportar_supuestos, construir_dwh, matlab, r) y tests/test_wiki_empresa.py
enlaces.json:  {"deps": {"BP2": ["M2"]}, "extra": {"BP2": "texto que se añade a hecho_cuando"}, "omitir": ["SI2"]}
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ_SKILL = AQUI.parent
CATALOGO = RAIZ_SKILL / "catalogo" / "capitulos.json"
PLANT = RAIZ_SKILL / "plantillas"
GANCHO = "import nodos_empresa  # wiki-de-empresa\nnodos_empresa.registrar(n)\n"

MODULO = '''"""VENDORIZADO desde la skill wiki-de-empresa: no se edita. Lo propio de la empresa vive en plan/enlaces_empresa.json."""
import json
from pathlib import Path

CATALOGO = {catalogo}
_ENLACES = Path(__file__).resolve().parent / "enlaces_empresa.json"


def registrar(n):
    enl = json.loads(_ENLACES.read_text(encoding="utf-8")) if _ENLACES.exists() else {{}}
    omitir = set(enl.get("omitir", []))
    for c in CATALOGO["nodos"]:
        if c["id"] in omitir:
            continue
        deps = [d for d in c["depende_de"] if d not in omitir] + enl.get("deps", {{}}).get(c["id"], [])
        extra = enl.get("extra", {{}}).get(c["id"])
        hecho = c["hecho_cuando"] + ("; " + extra if extra and extra not in c["hecho_cuando"] else "")
        entrega = ("docs/empresa/" + c["entrega"]) if c["entrega_base"] == "empresa" else c["entrega"]
        n(c["id"], c.get("fase", CATALOGO["fase"]), c["tipo"], c["titulo"], deps, entrega, hecho, c["cubre"])
'''

TEST = '''"""Lo vendorizado de wiki-de-empresa no ha divergido, y los capítulos cerrados cumplen su auditoría."""
import hashlib
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SKILL = Path("/mnt/f/skills/_personales/wiki-de-empresa")


def test_el_modulo_vendorizado_no_ha_divergido():
    import pytest
    if not SKILL.is_dir():
        pytest.skip("la skill no está montada; el repo sigue siendo autónomo")
    r = subprocess.run([sys.executable, str(SKILL / "scripts" / "instalar.py"), str(RAIZ), "--empresa", "x", "--comprobar"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_la_auditoria_de_la_wiki_corporativa_pasa():
    import pytest
    if not SKILL.is_dir():
        pytest.skip("la skill no está montada")
    r = subprocess.run([sys.executable, str(RAIZ / "plan" / "auditar_empresa.py"), str(RAIZ)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
'''


def render_modulo() -> str:
    cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
    return MODULO.format(catalogo=json.dumps(cat, ensure_ascii=False, indent=1))


def esqueleto(c: dict, empresa: str, hoy: str, enlaces: dict) -> str:
    secs = "".join(f"## {s}\n\n_(pendiente)_\n\n" for s in c["secciones"])
    ins = ", ".join(dict.fromkeys(c["enlaces_sugeridos"] + enlaces.get("deps", {}).get(c["id"], []))) or "(ninguno declarado)"
    return (PLANT / "capitulo.md.tpl").read_text(encoding="utf-8").format(
        titulo=c["titulo"], id=c["id"], fecha=hoy, empresa=empresa, hecho_cuando=c["hecho_cuando"], enlaces=ins, secciones=secs)


def main() -> int:
    a = argparse.ArgumentParser()
    a.add_argument("repo", type=Path)
    a.add_argument("--empresa", required=True)
    a.add_argument("--enlaces", type=Path)
    a.add_argument("--aplicar", action="store_true")
    a.add_argument("--comprobar", action="store_true", help="solo verifica que plan/nodos_empresa.py coincide con la skill")
    o = a.parse_args()
    repo = o.repo
    mod = repo / "plan" / "nodos_empresa.py"
    if o.comprobar:
        if not mod.exists() or mod.read_text(encoding="utf-8") != render_modulo():
            print("✗ plan/nodos_empresa.py diverge de la skill: corre instalar.py --aplicar")
            return 1
        aud = repo / "plan" / "auditar_empresa.py"
        if not aud.exists() or aud.read_text(encoding="utf-8") != (Path(__file__).parent / "auditar.py").read_text(encoding="utf-8"):
            print("✗ plan/auditar_empresa.py diverge de la skill: corre instalar.py --aplicar")
            return 1
        print("✓ vendorizado al día")
        return 0
    if not (repo / "plan" / "dag.py").exists() or not (repo / "plan" / "construir_dag.py").exists():
        print("✗ el repo no tiene el DAG estándar: instala primero dag-de-proyecto")
        return 2
    hoy = datetime.date.today().isoformat()
    enlaces = json.loads(o.enlaces.read_text(encoding="utf-8")) if o.enlaces else {}
    cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
    omitir = set(enlaces.get("omitir", []))
    acciones, escribir = [], []
    escribir.append((mod, render_modulo(), True))
    escribir.append((repo / "plan" / "auditar_empresa.py", (Path(__file__).parent / "auditar.py").read_text(encoding="utf-8"), True))
    if o.enlaces:
        escribir.append((repo / "plan" / "enlaces_empresa.json", json.dumps(enlaces, ensure_ascii=False, indent=1) + "\n", False))
    emp = repo / "docs" / "empresa"
    escribir.append((emp / "00_ARQUITECTURA_CORPORATIVA.md",
                     (PLANT / "arquitectura.md.tpl").read_text(encoding="utf-8").format(empresa=o.empresa, fecha=hoy), False))
    for c in cat["nodos"]:
        if c["id"] in omitir or c["entrega_base"] != "empresa" or not c["entrega"].endswith(".md"):
            continue
        if c["id"] == "SI0":
            txt = (PLANT / "sistemas" / "SI0_ARQUITECTURA.md.tpl").read_text(encoding="utf-8").format(empresa=o.empresa, fecha=hoy)
        elif c["id"] in ("BP99", "BP0"):
            continue
        else:
            txt = esqueleto(c, o.empresa, hoy, enlaces)
        escribir.append((emp / c["entrega"], txt, False))
    escribir.append((emp / "sistemas" / "SI1_ESQUEMA.sql", (PLANT / "sistemas" / "SI1_ESQUEMA.sql").read_text(encoding="utf-8"), False))
    for src, dst in (("construir_dwh.py", "analisis/dwh/construir_dwh.py"), ("exportar_supuestos.py", "analisis/exportar_supuestos.py"),
                     ("viabilidad.m", "analisis/matlab/viabilidad.m"), ("resumen.R", "analisis/r/resumen.R"),
                     ("cargar_abiertos.py", "analisis/dwh/cargar_abiertos.py")):
        escribir.append((repo / dst, (PLANT / "analisis" / src).read_text(encoding="utf-8"), False))
    escribir.append((repo / "docs" / "validacion" / "generar_paquetes.py",
                     (PLANT / "validacion" / "generar_paquetes.py").read_text(encoding="utf-8"), False))
    escribir.append((repo / "tests" / "test_wiki_empresa.py", TEST, False))
    for ruta, txt, pisa in escribir:
        existe = ruta.exists()
        acciones.append(f"{'actualizar' if existe and pisa else 'omitir (ya existe)' if existe else 'crear'} {ruta.relative_to(repo)}")
        if o.aplicar and (pisa or not existe):
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(txt, encoding="utf-8")
    cd = repo / "plan" / "construir_dag.py"
    t = cd.read_text(encoding="utf-8")
    if GANCHO not in t:
        acciones.append("enganchar nodos_empresa en plan/construir_dag.py")
        if o.aplicar:
            m = re.search(r"\n\ndef emitir\(", t)
            if not m:
                print("✗ no encuentro `def emitir(` en construir_dag.py")
                return 2
            cd.write_text(t[:m.start()] + "\n\n" + GANCHO + t[m.start():], encoding="utf-8")
    print(("aplicado" if o.aplicar else "ensayo") + f" en {repo}:\n  " + "\n  ".join(acciones))
    if not o.aplicar:
        print("(ensayo; --aplicar para escribir)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
