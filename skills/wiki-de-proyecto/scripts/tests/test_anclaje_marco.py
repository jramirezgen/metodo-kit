#!/usr/bin/env python3
"""Regla 0·ter: la nota puerta tiene `## Marco`, y una incidencia con
`intentos: N ≥ 2` sin `reanclaje:` avisa.

Uso: python3 scripts/tests/test_anclaje_marco.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import publicar as P  # noqa: E402


def ok(titulo: str, condicion: bool, detalle: str = "") -> bool:
    print(f"  {'✓' if condicion else '✗'} {titulo}"
          + (f" → {detalle}" if detalle and not condicion else ""))
    return condicion


def inc(carpeta: Path, nombre: str, fm: str) -> None:
    (carpeta / nombre).write_text(f"---\n{fm}\n---\n\n# x\n", encoding="utf-8")


def main() -> int:
    r: list[bool] = []
    with tempfile.TemporaryDirectory() as d:
        raiz = Path(d)
        puerta = raiz / "X.md"
        carpeta = raiz / "Incidencias"
        carpeta.mkdir()

        puerta.write_text("# X\n\n## Objetivo\n- a: pausado\n", encoding="utf-8")
        av = P.avisos_de_anclaje(puerta, carpeta)
        r.append(ok("sin `## Marco` avisa", any("## Marco" in a for a in av), str(av)))

        puerta.write_text("# X\n\n## Marco\nUexküll + Thomas antes de buscar.\n",
                          encoding="utf-8")
        r.append(ok("con `## Marco` y sin incidencias no avisa",
                    P.avisos_de_anclaje(puerta, carpeta) == []))

        inc(carpeta, "INC-001 — uno.md", "situacion: abierta\nintentos: 1")
        r.append(ok("1 intento no avisa", P.avisos_de_anclaje(puerta, carpeta) == []))

        inc(carpeta, "INC-002 — ocho.md", "situacion: abierta\nintentos: 8")
        av = P.avisos_de_anclaje(puerta, carpeta)
        r.append(ok("8 intentos sin reanclaje avisa",
                    len(av) == 1 and "INC-002" in av[0], str(av)))

        inc(carpeta, "INC-002 — ocho.md",
            "situacion: abierta\nintentos: 8\nreanclaje: 2026-10-12 auditoría conceptual")
        r.append(ok("con reanclaje no avisa", P.avisos_de_anclaje(puerta, carpeta) == []))

        inc(carpeta, "INC-003 — cerrada.md", "situacion: resuelta\nintentos: 5")
        r.append(ok("resuelta no avisa", P.avisos_de_anclaje(puerta, carpeta) == []))

        inc(carpeta, "INC-004 — rara.md", "situacion: abierta\nintentos: muchos")
        r.append(ok("intentos no numérico se ignora",
                    P.avisos_de_anclaje(puerta, carpeta) == []))

        r.append(ok("sin carpeta de incidencias no rompe",
                    P.avisos_de_anclaje(puerta, None) == []))
    print(f"{sum(r)}/{len(r)}")
    return 0 if all(r) else 1


if __name__ == "__main__":
    sys.exit(main())
