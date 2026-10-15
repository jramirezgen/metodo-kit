#!/usr/bin/env python3
"""Comprobación previa a una tanda de cómputo caro.

No adivina el diseño: contesta las preguntas de la lista de la skill que se pueden
contestar mecánicamente, y deja las demás a la vista.

    python3 preflight_tanda.py --motor edo
    python3 preflight_tanda.py --motor milp --instancia ELEMENT_CPLEX_THREADS ELEMENT_CPLEX_DETERMINISTIC
    python3 preflight_tanda.py --huella datos/banco.npz datos/paisaje.npz
    python3 preflight_tanda.py --sellos resultados/            # grafo de `consume` (regla 4b)

Salida: un informe y un código de salida (0 = nada que objetar, 1 = hay avisos).
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

BLAS = ["OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"]


def sha12(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for tramo in iter(lambda: f.read(1 << 20), b""):
            h.update(tramo)
    return h.hexdigest()[:12]


def sha_dict(d: dict) -> str:
    import hashlib as _h, json as _j
    d = {k: v for k, v in d.items() if k != "sha256"}
    return _h.sha256(_j.dumps(d, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def revisa_sellos(dirjson: Path) -> list[str]:
    """Regla 4b: ningun artefacto puede consumir un sello que ya no es el vigente.

    Un `consume` con sha caduco significa que el insumo se REGENERO DESPUES, o sea que el
    artefacto habla de otra corrida. Es el defecto que se cuela cuando el guion de la tanda
    corre los pasos en el orden en que se escribieron y no en el del grafo de dependencias.
    """
    import json as _j
    avisos: list[str] = []
    D = {}
    for q in sorted(dirjson.glob("*.json")):
        try:
            D[q.name] = _j.loads(q.read_text(encoding="utf-8"))
        except Exception as ex:
            avisos.append(f"{q.name} no es JSON legible: {ex}")
    sin_sello = [n for n, d in D.items() if "sha256" not in d]
    rotos = [n for n, d in D.items() if "sha256" in d and sha_dict(d) != d["sha256"]]
    caducos = []
    for n, d in D.items():
        for m, v in (d.get("consume") or {}).items():
            if m.startswith("_") or m not in D or "sha256" not in D[m]:
                continue
            if D[m]["sha256"] != v:
                caducos.append(f"{n} consume {m} con {str(v)[:12]}, vigente "
                               f"{D[m]['sha256'][:12]}")
    print(f"sellos         : {len(D)} artefactos, {len(sin_sello)} sin sello, "
          f"{len(rotos)} con sha que no cuadra, {len(caducos)} con `consume` caduco")
    if sin_sello:
        avisos.append(f"sin sello: {sin_sello}")
    if rotos:
        avisos.append(f"editados despues de sellarse: {rotos}")
    for c in caducos:
        avisos.append(f"SELLO CADUCO — {c}. Su insumo se regenero DESPUES: el artefacto habla "
                      f"de otra corrida y hay que re-derivarlo, no re-leerlo")
    return avisos


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--motor", choices=["edo", "milp", "replicas", "mixto"],
                    help="qué motor domina la tanda")
    ap.add_argument("--instancia", nargs="*", default=[],
                    help="variables de entorno que forman parte de la INSTANCIA")
    ap.add_argument("--huella", nargs="*", default=[],
                    help="ficheros de entrada cuyo hash debe ir en el nombre de la cache")
    ap.add_argument("--sellos", default=None,
                    help="directorio de artefactos .json con `consume` y `sha256`: comprueba "
                         "que ninguno consuma un sello CADUCO (regla 4b)")
    a = ap.parse_args()
    avisos: list[str] = []

    ncpu = os.cpu_count() or 0
    try:
        carga = os.getloadavg()[0]
    except OSError:
        carga = float("nan")
    print(f"maquina        : {ncpu} nucleos, load1 {carga:.2f}")
    if carga > 0.5 * ncpu:
        avisos.append(f"la maquina ya esta al {carga / max(ncpu, 1):.0%}: un solve con limite "
                      f"de tiempo de PARED puede vaciarse por el cronometro, no por el problema")

    fijados = {v: os.environ.get(v) for v in BLAS}
    a_uno = [v for v, x in fijados.items() if x == "1"]
    print("hilos de BLAS  : " + (", ".join(f"{v}={x}" for v, x in fijados.items() if x)
                                 or "ninguno fijado (por defecto = todos los nucleos)"))

    if a.motor in ("edo", "replicas", "mixto"):
        if not a_uno:
            avisos.append("motor de un solo nucleo con los hilos de BLAS SIN fijar: cada "
                          "trabajador girara hilos que no usa y saturaras la maquina con menos "
                          "procesos de los que caben. Exporta OMP/MKL/OPENBLAS_NUM_THREADS=1 y "
                          "paraleliza POR CASO")
        else:
            print(f"               -> correcto: {len(a_uno)} variables a 1, paraleliza por caso")
    if a.motor in ("milp", "mixto"):
        print("motor MILP     : el solver paraleliza DENTRO del B&B -> un caso a la vez, "
              "con la maquina entera")

    for v in a.instancia:
        x = os.environ.get(v)
        if x is None:
            avisos.append(f"{v} NO esta fijada: su valor por defecto suele ser os.cpu_count(), "
                          f"asi que la instancia cambia de maquina a maquina sin que nadie "
                          f"escriba nada. Fijala y publicala junto al hash de la entrada")
        else:
            print(f"instancia      : {v}={x}  (publicalo con el resultado)")

    for f in a.huella:
        p = Path(f)
        if not p.is_file():
            avisos.append(f"no existe la entrada {f}, no puedo darte su huella")
            continue
        print(f"huella         : {p.name}  {sha12(p)}   <- mete esto en el nombre de la cache")

    if a.sellos:
        avisos += revisa_sellos(Path(a.sellos))

    if avisos:
        print("\nAVISOS:")
        for x in avisos:
            print(f"  ! {x}")
    else:
        print("\nsin objeciones mecanicas. Las preguntas 4-6 de la lista son de criterio y no "
              "las puede contestar un script:\n"
              "  4. el nombre de cada artefacto reanudable lleva el hash de sus entradas?\n"
              "  5. alguna lectura de resultado tiene un `default`, o copie la clave de la "
              "firma de ENTRADA en vez de la de SALIDA?\n"
              "  6. copie alguna omision de otra fase sin copiar la compuerta que la "
              "justificaba?")
    return 1 if avisos else 0


if __name__ == "__main__":
    raise SystemExit(main())
