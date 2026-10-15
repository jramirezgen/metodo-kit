#!/usr/bin/env python3
"""Compuerta de la compuerta: `vault_audit.py` no puede inventar enlaces rotos.

⛔ **El defecto que esto cierra, medido el 2026-09-08.** Al publicar los dos
`.canvas` de ELEMENT en `wiki/ELEMENT/` y enlazarlos desde su nota, el auditor
reportó **2 enlaces rotos** con los dos ficheros presentes en disco y Obsidian
abriéndolos sin problema. La causa: `resolubles` se construía sólo con los
`.md`, así que **todo enlace a un adjunto —`.canvas`, `.png`, `.pdf`— era roto
por construcción**. Y `certificar.sh` falla con un solo enlace roto, o sea que
la compuerta del vault quedaba en rojo permanente por publicar un mapa.

Un falso positivo en una compuerta cuesta lo mismo que un falso negativo: la
siguiente vez que salga rojo, nadie lo va a mirar.

Uso: python3 scripts/tests/test_vault_audit.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import vault_audit  # noqa: E402

FRONTMATTER = """---
tags: [prueba]
area: [Sistema]
tema: [Prueba]
creado: 2026-09-08
actualizado: 2026-09-08
fuente: "sintetico"
---
"""


def _vault(tmp: Path, cuerpo_nota: str, adjuntos: tuple[str, ...] = ()) -> Path:
    (tmp / "wiki" / "PRUEBA").mkdir(parents=True)
    (tmp / "wiki" / "PRUEBA" / "Nota.md").write_text(FRONTMATTER + cuerpo_nota, encoding="utf-8")
    (tmp / "index.md").write_text("# index\n\n- [[Nota]]\n", encoding="utf-8")
    for nombre in adjuntos:
        (tmp / "wiki" / "PRUEBA" / nombre).write_text("{}", encoding="utf-8")
    return tmp


def caso(titulo: str, cuerpo: str, adjuntos: tuple[str, ...], esperados: int) -> bool:
    with tempfile.TemporaryDirectory() as d:
        g = vault_audit.medir(_vault(Path(d), cuerpo, adjuntos))["grafo"]
        obtenidos = len(g["enlaces_rotos"])
        ok = obtenidos == esperados
        print(f"  {'✓' if ok else '✗'} {titulo}: {obtenidos} rotos (esperados {esperados})"
              + ("" if ok else f" → {sorted(g['enlaces_rotos'])}"))
        return ok


def main() -> int:
    print("vault_audit — resolución de enlaces a adjuntos")
    resultados = [
        caso("un .canvas que existe no es un enlace roto",
             "- [[Mapa del sistema.canvas|el mapa]]\n", ("Mapa del sistema.canvas",), 0),
        caso("un .canvas que NO existe sigue siendo un enlace roto",
             "- [[Mapa fantasma.canvas]]\n", (), 1),
        caso("un adjunto que no es .canvas tambien resuelve",
             "- [[diagrama.png]]\n", ("diagrama.png",), 0),
        caso("una nota .md ausente sigue siendo un enlace roto",
             "- [[Nota que no existe]]\n", (), 1),
        # 99b9f1a (2026-09-28): en una tabla el alias va como `[[Nota\|alias]]` y
        # Obsidian resuelve `Nota`; sin quitar la barra contaban 9 rotos falsos.
        caso("[[Nota\\|alias]] en una tabla resuelve a Nota",
             "| a | b |\n|---|---|\n| [[Nota\\|la nota]] | x |\n", (), 0),
        caso("[[Fantasma\\|alias]] en una tabla sigue siendo roto",
             "| a | b |\n|---|---|\n| [[Fantasma\\|alias]] | x |\n", (), 1),
    ]
    ok = vault_audit.enlaces_de("| [[Nota\\|x]] |") == ["Nota"]
    print(f"  {'✓' if ok else '✗'} enlaces_de quita la barra del alias escapado")
    resultados.append(ok)
    print(f"\n{sum(resultados)}/{len(resultados)} verde")
    return 0 if all(resultados) else 1


# --------------------------------------------------------------------------
# Sub-mapas declarados: un índice de colección no infla el índice maestro
# --------------------------------------------------------------------------

SUBMAPA = """---
tags: [indice]
area: [Sistema]
tema: [Prueba]
creado: 2026-09-08
actualizado: 2026-09-08
fuente: "sintetico"
submapa: true
---

# Índice de la colección

- [[Hija]]
"""

HIJA = FRONTMATTER + "\n# Hija\n"


def caso_submapa(titulo: str, declara: bool, enlazado: bool, esperadas: int) -> bool:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        (tmp / "wiki" / "P" / "Coleccion").mkdir(parents=True)
        texto = SUBMAPA if declara else SUBMAPA.replace("submapa: true\n", "")
        (tmp / "wiki" / "P" / "Coleccion" / "00 — Indice.md").write_text(texto, encoding="utf-8")
        (tmp / "wiki" / "P" / "Coleccion" / "Hija.md").write_text(HIJA, encoding="utf-8")
        enlace = "- [[00 — Indice]]\n" if enlazado else ""
        (tmp / "index.md").write_text(f"# index\n\n{enlace}", encoding="utf-8")
        m = vault_audit.medir(tmp)
        obtenidas = m["disciplina"]["indexadas"]
        total = m["escala"]["notas"]
        ok = obtenidas == esperadas
        print(f"  {'✓' if ok else '✗'} {titulo}: {obtenidas}/{total} indexadas "
              f"(esperadas {esperadas})")
        return ok


def caso_submapa_anidado(titulo: str, declara: bool, esperadas: int) -> bool:
    """El índice de colección lo enlaza un SUB-MAPA de la raíz, no `index.md`.

    ⛔ Es la forma real, no un caso de laboratorio: las notas de ELEMENT viven
    en `index_TGDE.md`, no en el índice maestro. Meter sus colecciones en
    `index.md` sería devolver al mapa maestro justo el detalle de proyecto que
    la partición del 2026-09-07 le quitó. El recorrido tiene que ser
    **transitivo**: un sub-mapa de un sub-mapa sigue siendo mapa.
    """
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        (tmp / "wiki" / "P" / "Coleccion").mkdir(parents=True)
        texto = SUBMAPA if declara else SUBMAPA.replace("submapa: true\n", "")
        (tmp / "wiki" / "P" / "Coleccion" / "00 — Indice.md").write_text(texto, encoding="utf-8")
        (tmp / "wiki" / "P" / "Coleccion" / "Hija.md").write_text(HIJA, encoding="utf-8")
        (tmp / "index.md").write_text("# index\n\n- [[index_RAMA]]\n", encoding="utf-8")
        (tmp / "index_RAMA.md").write_text("# rama\n\n- [[00 — Indice]]\n", encoding="utf-8")
        m = vault_audit.medir(tmp)
        obtenidas = m["disciplina"]["indexadas"]
        total = m["escala"]["notas"]
        ok = obtenidas == esperadas
        print(f"  {'✓' if ok else '✗'} {titulo}: {obtenidas}/{total} indexadas "
              f"(esperadas {esperadas})")
        return ok


def main_submapas() -> int:
    print("\nvault_audit — un indice de coleccion declarado hace de sub-mapa")
    r = [
        caso_submapa("declarado y enlazado: sus hijas cuentan como indexadas", True, True, 2),
        caso_submapa("declarado pero NO enlazado: no arrastra a nadie", True, False, 0),
        caso_submapa("enlazado pero NO declarado: tampoco arrastra", False, True, 1),
        caso_submapa_anidado("declarado y enlazado DESDE UN SUB-MAPA: cuenta igual", True, 2),
        caso_submapa_anidado("sin declarar, aunque lo enlace un sub-mapa: no arrastra", False, 1),
    ]
    print(f"\n{sum(r)}/{len(r)} verde")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main() or main_submapas())
