#!/usr/bin/env python3
"""Genera `.obsidian/graph.json`: la configuración de la vista de grafo.

El problema que resuelve (medido 2026-08-01): la vista de grafo de Obsidian
indexa **todos** los `.md` del vault. Con 5.128 archivos de los cuales solo 178
son notas de `wiki/`, el grafo real queda sepultado bajo ~4.950 puntos sueltos
de `raw/` y `alejandria/`. El filtro por defecto (`search: ""`) no excluye nada
y `showOrphans: true` los dibuja todos.

La corrección es un filtro de búsqueda + grupos de color por carpeta. Se genera
en vez de escribirse a mano por la misma razón que el catálogo de Alejandría:
al aparecer una carpeta nueva en `wiki/`, un JSON mantenido a mano se queda sin
su color y nadie se entera.

Uso:
    python3 generar_grafo.py /mnt/f/OBSIDIAN              # simulacro
    python3 generar_grafo.py /mnt/f/OBSIDIAN --aplicar    # escribe
    python3 generar_grafo.py /mnt/f/OBSIDIAN --incluir-alejandria --aplicar
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path

# Paleta fija y ordenada. La asignación carpeta->color es determinista (por
# orden alfabético de carpeta), así que dos ejecuciones dan el mismo resultado
# y añadir una carpeta no reordena los colores ya establecidos... salvo que la
# nueva se intercale. Por eso ANCLAS fija las carpetas conocidas.
PALETA = [
    "#4C8DFF",  # azul
    "#45C06B",  # verde
    "#F0A02E",  # ámbar
    "#A97BFF",  # violeta
    "#FF6B9D",  # magenta
    "#2ECFCF",  # cian
    "#E5534B",  # rojo
    "#C3D94A",  # lima
    "#9AA5B1",  # gris
    "#FF9F5A",  # naranja
    "#7FD1FF",  # celeste
    "#D48AFF",  # lila
]

# Carpetas con color reservado: el significado del color no cambia aunque
# aparezcan carpetas nuevas. Las no listadas toman los colores sobrantes.
ANCLAS = {
    "PRINCIPIA": "#A97BFF",   # teoría — el tronco
    "ELEMENT": "#4C8DFF",     # el motor
    "SHEWANELLA": "#45C06B",  # validación
    "HAMCAO": "#F0A02E",      # validación
    "ECOLI": "#2ECFCF",       # validación
    "EMPRESA": "#FF6B9D",     # negocio
    "CIMMA": "#FF9F5A",       # negocio
    "SISTEMA": "#9AA5B1",     # infraestructura
    "AREAS": "#E5534B",       # navegación
}


def a_rgb_int(hex_color: str) -> int:
    """'#4C8DFF' -> 5017087. Obsidian guarda el color como entero decimal."""
    return int(hex_color.lstrip("#"), 16)


def carpetas_wiki(vault: Path) -> list[tuple[str, int]]:
    """Carpetas de primer nivel de wiki/ con su nº de notas, mayor primero."""
    wiki = vault / "wiki"
    if not wiki.is_dir():
        sys.exit(f"error: no existe {wiki}")
    out = []
    for d in sorted(p for p in wiki.iterdir() if p.is_dir()):
        n = len(list(d.rglob("*.md")))
        if n:
            out.append((d.name, n))
    return sorted(out, key=lambda t: -t[1])


def asignar_colores(nombres: list[str]) -> dict[str, str]:
    usados = {ANCLAS[n] for n in nombres if n in ANCLAS}
    libres = [c for c in PALETA if c not in usados]
    fuera = iter(libres)
    colores = {}
    for n in nombres:
        colores[n] = ANCLAS.get(n) or next(fuera, "#9AA5B1")
    return colores


def construir(vault: Path, incluir_alejandria: bool) -> dict:
    carpetas = carpetas_wiki(vault)
    nombres = [n for n, _ in carpetas]
    colores = asignar_colores(nombres)

    # El filtro es lo que salva el grafo: sin él Obsidian dibuja los 5.128 .md
    # del vault. `path:` acepta prefijo de ruta, igual que la búsqueda global.
    ambito = "path:wiki/"
    if incluir_alejandria:
        ambito = "(path:wiki/ OR path:alejandria/)"

    grupos = [
        {
            "query": f"path:wiki/{nombre}/",
            "color": {"a": 1, "rgb": a_rgb_int(colores[nombre])},
        }
        for nombre, _ in carpetas
    ]
    if incluir_alejandria:
        grupos.append(
            {"query": "path:alejandria/", "color": {"a": 1, "rgb": a_rgb_int("#6B7684")}}
        )

    return {
        "collapse-filter": False,
        "search": ambito,
        "showTags": False,
        "showAttachments": False,
        # Un enlace a una nota inexistente dibuja un nodo fantasma. Con 1.917
        # enlaces conviene ocultarlos: el audit ya vigila que sean 0 enlaces
        # rotos, y aquí solo ensucian.
        "hideUnresolved": True,
        # Falso a propósito: wiki/ tiene 0 islas medidas, así que un huérfano
        # en pantalla es señal de nota mal enlazada, no de ruido esperado.
        "showOrphans": False,
        "collapse-color-groups": False,
        "colorGroups": grupos,
        "collapse-display": False,
        "showArrow": True,
        # 0 dejaba las etiquetas invisibles salvo con mucho zoom. Con 178 nodos
        # caben los nombres.
        "textFadeMultiplier": -0.7,
        "nodeSizeMultiplier": 1.15,
        "lineSizeMultiplier": 0.8,
        "collapse-forces": False,
        "centerStrength": 0.42,
        # 10.8 enlaces por nota: con linkStrength alto todo colapsa a una bola.
        # Bajarlo y subir la repulsión es lo que separa los clusters temáticos.
        "repelStrength": 13,
        "linkStrength": 0.55,
        "linkDistance": 190,
        "scale": 0.75,
        "close": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("vault", type=Path)
    ap.add_argument("--aplicar", action="store_true", help="escribe graph.json")
    ap.add_argument(
        "--incluir-alejandria",
        action="store_true",
        help="añade alejandria/ al grafo (859 notas más; por defecto fuera)",
    )
    args = ap.parse_args()

    vault = args.vault.resolve()
    destino = vault / ".obsidian" / "graph.json"
    cfg = construir(vault, args.incluir_alejandria)

    total_md = len(list(vault.rglob("*.md")))
    en_grafo = len(list((vault / "wiki").rglob("*.md")))
    if args.incluir_alejandria:
        en_grafo += len(list((vault / "alejandria").rglob("*.md")))

    print(f"# Grafo de Obsidian — {date.today().isoformat()}")
    print(f"\n`.md` en el vault ............ {total_md:,}")
    print(f"nodos tras el filtro ........ {en_grafo:,}")
    print(f"ruido excluido .............. {total_md - en_grafo:,} "
          f"({100 * (total_md - en_grafo) / total_md:.1f}%)")
    print(f"\nfiltro: {cfg['search']}")
    print("\ngrupos de color:")
    for nombre, n in carpetas_wiki(vault):
        c = next(g for g in cfg["colorGroups"] if g["query"] == f"path:wiki/{nombre}/")
        print(f"  {nombre:<14} {n:>4} notas  #{c['color']['rgb']:06X}")

    if not args.aplicar:
        print("\n(simulacro — usa --aplicar para escribir)")
        return 0

    if destino.exists():
        copia = destino.with_suffix(f".json.bak-{date.today().isoformat()}")
        shutil.copy2(destino, copia)
        print(f"\nrespaldo: {copia.name}")
    destino.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"escrito: {destino}")
    print("\nObsidian cachea graph.json: cierra y reabre la bóveda para verlo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
