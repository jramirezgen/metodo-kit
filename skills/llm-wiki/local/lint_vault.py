#!/usr/bin/env python3
"""
lint_vault.py — el linter de llm-wiki, adaptado a ESTE vault.

`scripts/lint_wiki.py` da por supuesto un vault recien creado por `init_vault.py`:
una sola carpeta `wiki/`, enlaces que apuntan solo dentro de ella, y un frontmatter
`title/category/summary`. Aqui no se cumple ninguna de las tres cosas, y medido el
2026-09-09 sobre /mnt/f/OBSIDIAN el linter de origen daba:

    554 enlaces rotos    de los que 11 lo estaban de verdad  (98 % de falsos)
    706 notas sin frontmatter  de 706  (el esquema local es area:/tema:)

Las tres diferencias, y como las resuelve este envoltorio:

  1. Alejandria y la raiz son destinos legitimos. Un `[[alejandria/COL/AL-0549_x]]`
     no es un enlace roto: es la transclusion que manda el protocolo.
  2. **Los mapas son ficheros.** `.canvas` (JSON Canvas) y `.base` (base nativa de
     Obsidian) los publica la skill `wiki-de-proyecto` y se enlazan como cualquier
     nota. El linter de origen solo miraba `.md`, asi que declaraba rota toda la
     arquitectura de canvas.
  3. El frontmatter obligatorio aqui es `area:` (vocabulario cerrado de nueve) y
     `tema:` (abierto). No `category`.

Lo que NO hace: contar notas, tokens o peso. Esas cifras salen de
`vault-ops/scripts/vault_audit.py` y de ningun otro sitio.

Uso:
    python3 local/lint_vault.py                      # /mnt/f/OBSIDIAN
    python3 local/lint_vault.py --vault RUTA --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

VAULT_POR_DEFECTO = Path("/mnt/f/OBSIDIAN")

# Un enlace puede apuntar a cualquiera de estos. `.canvas` y `.base` son la
# arquitectura de mapas, no adjuntos.
EXTENSIONES_ENLAZABLES = {".md", ".canvas", ".base", ".csv", ".png", ".pdf"}

# Nunca se recorren: coste, ruido o secretos.
EXCLUIDOS = {
    ".obsidian", ".git", ".trash", "_PRIVADO", "node_modules",
    ".venv", "dist", "archive", "__pycache__", "skills",
    "_archivo_boveda-duplicada-2026-07-28",
}

# Se indexan como destino pero no se leen ni se lintan. `_archivo_*`, `_graphify`
# y las skills vendorizadas en la raiz son destinos validos, no material a auditar.
NO_SE_LINTAN = {"raw", "alejandria", "_graphify", "stop-slop", "_PLANTILLA Proyecto.md"}

# Solo se lintan estas fuentes: la wiki y los mapas de la raiz. CLAUDE.md y AGENTS.md
# contienen `[[Nota]]`, `[[ruta completa]]` y demas ejemplos en prosa; no son enlaces.
def _es_fuente(rel) -> bool:
    partes = rel.parts
    if partes[0] == "wiki":
        return True
    return len(partes) == 1 and (partes[0] == "index.md" or partes[0].startswith("index_"))

AREAS = {
    "Investigación", "Empresa", "Sistema", "Conocimiento",
    "Relaciones", "Clientes", "Finanzas", "Salud", "Talleres",
}

# `(?<!!)`: una transclusion `![[x]]` no es un enlace roto aunque `x` no
# exista como nota suelta --- es la misma regla que usa check_docs_graph.py
# del repo. Sin ella, un ejemplo de sintaxis escrito en prosa sale como
# averia, y una compuerta que grita se ignora.
ENLACE = re.compile(r"(?<!!)\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")

# Los mapas versionados los genera `wiki-de-proyecto` y son hojas por diseño:
# nadie los enlaza porque su indice es la `.base` de versiones.
GENERADO = re.compile(r"/Mapas/Versiones/|_PLANTILLA ")


def _excluido(rel: Path) -> bool:
    return any(p in EXCLUIDOS for p in rel.parts)


def indexar(vault: Path):
    """Todo destino enlazable del vault, por ruta relativa y por nombre."""
    por_ruta: set[str] = set()
    por_nombre: dict[str, list[str]] = defaultdict(list)
    lintables: list[Path] = []
    for f in vault.rglob("*"):
        if not f.is_file() or f.suffix not in EXTENSIONES_ENLAZABLES:
            continue
        rel = f.relative_to(vault)
        if _excluido(rel):
            continue
        r = str(rel).replace("\\", "/")
        por_ruta.add(r)
        if r.endswith(".md"):
            por_ruta.add(r[:-3])
        por_nombre[f.name].append(r)
        if f.suffix == ".md":
            por_nombre[f.stem].append(r)
            if rel.parts[0] not in NO_SE_LINTAN and _es_fuente(rel):
                lintables.append(f)
    return por_ruta, por_nombre, lintables


def frontmatter(texto: str) -> dict:
    if not texto.startswith("---"):
        return {}
    fin = texto.find("\n---", 3)
    if fin == -1:
        return {}
    campos: dict[str, str] = {}
    for linea in texto[3:fin].splitlines():
        if ":" in linea and not linea.startswith((" ", "-", "\t")):
            k, _, v = linea.partition(":")
            campos[k.strip()] = v.strip()
    return campos


def analizar(vault: Path) -> dict:
    por_ruta, por_nombre, lintables = indexar(vault)

    rotos: list[dict] = []
    entrantes: dict[str, int] = defaultdict(int)
    sin_area: list[str] = []
    area_invalida: list[dict] = []
    sin_tema: list[str] = []

    for f in lintables:
        rel = str(f.relative_to(vault)).replace("\\", "/")
        try:
            texto = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        fm = frontmatter(texto)
        if rel != "index.md" and not rel.startswith("index_"):
            crudo = fm.get("area", "")
            if not crudo:
                sin_area.append(rel)
            else:
                declaradas = [a.strip(" []'\"") for a in crudo.split(",") if a.strip(" []'\"")]
                fuera = [a for a in declaradas if a not in AREAS]
                if fuera:
                    area_invalida.append({"nota": rel, "fuera_del_vocabulario": fuera})
            if not fm.get("tema", ""):
                sin_tema.append(rel)

        for m in ENLACE.finditer(texto):
            destino = m.group(1).strip()
            if not destino:
                continue
            if destino in por_ruta:
                entrantes[destino] += 1
                continue
            cand = por_nombre.get(destino) or por_nombre.get(destino.split("/")[-1])
            if cand:
                entrantes[cand[0]] += 1
                if len(cand) > 1:
                    pass  # ambiguo, no es un roto
                continue
            rotos.append({"desde": rel, "destino": destino})

    huerfanas = [
        str(f.relative_to(vault)).replace("\\", "/")
        for f in lintables
        if not entrantes.get(str(f.relative_to(vault)).replace("\\", "/"))
        and not entrantes.get(str(f.relative_to(vault)).replace("\\", "/")[:-3])
        and not GENERADO.search("/" + str(f.relative_to(vault)).replace("\\", "/"))
        and str(f.relative_to(vault)) != "index.md"
    ]

    return {
        "vault": str(vault),
        "notas_lintadas": len(lintables),
        "enlaces_rotos": sorted(rotos, key=lambda r: r["destino"]),
        "huerfanas": sorted(huerfanas),
        "sin_area": sorted(sin_area),
        "area_fuera_del_vocabulario": area_invalida,
        "sin_tema": sorted(sin_tema),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", type=Path, default=VAULT_POR_DEFECTO)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if not (a.vault / "wiki").is_dir():
        print(f"[error] no hay wiki/ en {a.vault}", file=sys.stderr)
        return 1

    r = analizar(a.vault)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0

    print(f"vault: {r['vault']}  ({r['notas_lintadas']} notas lintadas)")
    print(f"  enlaces rotos          {len(r['enlaces_rotos'])}")
    for x in r["enlaces_rotos"]:
        print(f"      [[{x['destino']}]]  <-  {x['desde']}")
    print(f"  huérfanas (0 entrantes) {len(r['huerfanas'])}")
    for x in r["huerfanas"][:40]:
        print(f"      {x}")
    if len(r["huerfanas"]) > 40:
        print(f"      … y {len(r['huerfanas']) - 40} más")
    print(f"  sin area:               {len(r['sin_area'])}")
    print(f"  area fuera del vocab.   {len(r['area_fuera_del_vocabulario'])}")
    for x in r["area_fuera_del_vocabulario"][:20]:
        print(f"      {x['nota']}  ->  {x['fuera_del_vocabulario']}")
    print(f"  sin tema:               {len(r['sin_tema'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
