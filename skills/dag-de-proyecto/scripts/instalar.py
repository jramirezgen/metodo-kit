# -*- coding: utf-8 -*-
"""Instala o pone al día el DAG estándar en un repo. Decide por lo que encuentra:

    python3 instalar.py <repo> --proyecto NOMBRE --hoja REL-1.0.0           # ensayo
    python3 instalar.py <repo> --proyecto NOMBRE --hoja REL-1.0.0 --aplicar # estrena
    python3 instalar.py <repo> --aplicar                                    # re-copia SÓLO lo vendorizado

Nunca pisa plan/dag.json, plan/plan.json ni registro/: son del proyecto.
"""
import argparse
import json
import shutil
from pathlib import Path

AQUI = Path(__file__).resolve().parent
VENDORIZADO = ["dag_lib.py", "dag.py"]
TEST = '''"""Lo vendorizado de dag-de-proyecto no ha divergido de su skill, y el DAG del repo es válido."""
import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SKILL = Path("/mnt/f/skills/_personales/dag-de-proyecto/scripts")


@pytest.mark.parametrize("nombre", {vendorizado!r})
def test_lo_vendorizado_no_ha_divergido(nombre):
    if not SKILL.is_dir():
        pytest.skip("la skill no está montada; el repo sigue siendo autónomo")
    h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert h(RAIZ / "plan" / nombre) == h(SKILL / nombre), f"plan/{{nombre}} divergió: corre instalar.py --aplicar"


def test_el_dag_es_valido_y_estado_al_dia():
    r = subprocess.run([sys.executable, str(RAIZ / "plan" / "dag.py"), "estado", "--comprobar"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr + r.stdout
'''


def main():
    a = argparse.ArgumentParser()
    a.add_argument("repo", type=Path)
    a.add_argument("--proyecto")
    a.add_argument("--hoja")
    a.add_argument("--aplicar", action="store_true")
    o = a.parse_args()
    plan = o.repo / "plan"
    nuevo = not (plan / "dag.json").exists()
    if nuevo and not (o.proyecto and o.hoja):
        raise SystemExit("estrenar exige --proyecto y --hoja")
    acciones = [f"copiar {n} → plan/{n}" for n in VENDORIZADO] + ["escribir tests/test_dag_estandar.py"]
    if nuevo:
        acciones += ["sembrar plan/dag.json", "sembrar registro/nodos.jsonl vacío"]
    print(("estreno" if nuevo else "puesta al día") + f" de {o.repo}:\n  " + "\n  ".join(acciones))
    if not o.aplicar:
        print("(ensayo; --aplicar para escribir)")
        return
    plan.mkdir(exist_ok=True)
    for n in VENDORIZADO:
        shutil.copyfile(AQUI / n, plan / n)
    (o.repo / "tests").mkdir(exist_ok=True)
    (o.repo / "tests" / "test_dag_estandar.py").write_text(TEST.format(vendorizado=VENDORIZADO))
    if nuevo:
        (plan / "dag.json").write_text(json.dumps({"proyecto": o.proyecto, "hoja": o.hoja}, indent=2) + "\n")
        (o.repo / "registro").mkdir(exist_ok=True)
        (o.repo / "registro" / "nodos.jsonl").touch()
    print("hecho")


if __name__ == "__main__":
    main()
