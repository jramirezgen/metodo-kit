#!/usr/bin/env python3
"""Compuerta de una Base de Obsidian: una tabla vacía no es una tabla.

⛔ **El defecto que esto cierra.** Una `.base` se alimenta del frontmatter de
las notas que su filtro alcanza. Si el filtro no alcanza ninguna, o si ordena
por una propiedad que ninguna nota declara, Obsidian **no da ningún error**:
dibuja una tabla vacía o una columna en blanco. Es el mismo fallo que costó el
canvas con seis etiquetas detrás de un nodo — *una compuerta que nunca estuvo
roja puede estar verde por vacía* — y aquí es peor, porque una base vacía se
parece exactamente a «todavía no hay datos».

Uso: python3 scripts/tests/test_base_lib.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import base_lib  # noqa: E402

NOTA = """---
tags: [ecuacion]
ecuacion_id: E07
capa: "4 — cinética"
estado: validada
---

# Una ecuación
"""

NOTA_SIN_CAPA = """---
tags: [ecuacion]
ecuacion_id: E08
estado: validada
---

# Otra
"""


def _vault(tmp: Path, notas: dict[str, str]) -> Path:
    """Una bóveda de juguete **con su `.obsidian/`**.

    El marcador no es decorado: `en_carpeta()` deduce la raíz buscándolo hacia
    arriba, porque la ruta de un filtro es relativa a la bóveda que se abre y
    suponerla es lo que dejó dos Bases vacías sin un solo aviso. Una bóveda de
    prueba sin `.obsidian/` no es una bóveda, y este test lo daba por hecho.
    """
    (tmp / ".obsidian").mkdir()
    (tmp / "wiki" / "P" / "Ecuaciones").mkdir(parents=True)
    for nombre, texto in notas.items():
        (tmp / "wiki" / "P" / "Ecuaciones" / nombre).write_text(texto, encoding="utf-8")
    return tmp


def _base(raiz: Path, carpeta: str = "wiki/P/Ecuaciones",
          orden=("file.name", "capa", "estado")):
    # Absoluta a propósito: la relativa es justo el dato que depende de la raíz.
    return base_lib.Base(
        nombre="Ecuaciones",
        filtros=base_lib.en_carpeta(raiz / carpeta),
        vistas=[base_lib.Vista(tipo="table", nombre="Todas", orden=list(orden))],
    )


def caso(titulo: str, problemas, esperados: int, duros_esperados: int) -> bool:
    duros = [p for p in problemas if p.duro]
    ok = len(problemas) == esperados and len(duros) == duros_esperados
    print(f"  {'✓' if ok else '✗'} {titulo}: {len(problemas)} problemas "
          f"({len(duros)} duros), esperados {esperados}/{duros_esperados}")
    if not ok:
        for p in problemas:
            print(f"      {'DURO' if p.duro else 'aviso'} {p.regla}: {p.detalle}")
    return ok


def main() -> int:
    print("base_lib — una base que no alcanza notas no se publica")
    r = []

    with tempfile.TemporaryDirectory() as d:
        raiz = _vault(Path(d), {"E07.md": NOTA})
        r.append(caso("una base cuyas columnas existen en las notas pasa",
                      base_lib.validar(_base(raiz), raiz), 0, 0))

    with tempfile.TemporaryDirectory() as d:
        raiz = _vault(Path(d), {"E07.md": NOTA})
        r.append(caso("un filtro que no alcanza ninguna nota es DURO",
                      base_lib.validar(_base(raiz, carpeta="wiki/P/NoExiste"), raiz), 1, 1))

    with tempfile.TemporaryDirectory() as d:
        raiz = _vault(Path(d), {"E08.md": NOTA_SIN_CAPA})
        r.append(caso("una columna que ninguna nota declara es DURA",
                      base_lib.validar(_base(raiz), raiz), 1, 1))

    with tempfile.TemporaryDirectory() as d:
        raiz = _vault(Path(d), {"E07.md": NOTA, "E08.md": NOTA_SIN_CAPA})
        r.append(caso("una columna que sólo la mitad declara avisa, no bloquea",
                      base_lib.validar(_base(raiz), raiz), 1, 0))

    with tempfile.TemporaryDirectory() as d:
        raiz = _vault(Path(d), {"E07.md": NOTA})
        b = base_lib.Base(nombre="X",
                          filtros=base_lib.en_carpeta(raiz / "wiki/P/Ecuaciones"),
                          vistas=[base_lib.Vista(tipo="timeline", nombre="V", orden=["file.name"])])
        r.append(caso("un tipo de vista que Obsidian no tiene es DURO",
                      base_lib.validar(b, raiz), 1, 1))

    with tempfile.TemporaryDirectory() as d:
        raiz = _vault(Path(d), {"E07.md": NOTA})
        b = base_lib.Base(nombre="X",
                          filtros=base_lib.en_carpeta(raiz / "wiki/P/Ecuaciones"),
                          vistas=[])
        r.append(caso("una base sin ninguna vista es DURA",
                      base_lib.validar(b, raiz), 1, 1))

    print("\nbase_lib — el YAML que se emite es el que Obsidian lee")
    with tempfile.TemporaryDirectory() as d:
        y = _base(_vault(Path(d), {"E07.md": NOTA})).a_yaml()
    esperado = [
        "filters:",
        '    - file.inFolder("wiki/P/Ecuaciones")',
        "views:",
        "  - type: table",
        '    name: Todas',      # sin comillas: es lo que Obsidian escribe
        "    order:",
        "      - file.name",
        "      - capa",
    ]
    falta = [linea for linea in esperado if linea not in y.splitlines()]
    ok = not falta
    print(f"  {'✓' if ok else '✗'} el YAML trae filters/views/order"
          + ("" if ok else f" — faltan {falta}"))
    r.append(ok)
    if not ok:
        print(y)

    print(f"\n{sum(r)}/{len(r)} verde")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
