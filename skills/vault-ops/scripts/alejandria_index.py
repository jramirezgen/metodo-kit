#!/usr/bin/env python3
"""Genera el catálogo de Alejandría: la biblioteca de documentos extensos del vault.

Alejandría guarda **documentos largos enteros** (revisiones de investigación,
Deep Research, informes técnicos, apuntes densos) que valen por su texto completo
y no solo por su síntesis. Nunca se cargan enteros: se invocan por contexto y a
petición. Para eso hace falta un catálogo **superficial pero decisorio** — que
permita decidir si abrir un documento sin abrirlo.

Este script lo genera. El catálogo no se escribe a mano: se regenera.

Uso:
    python alejandria_index.py <raiz_vault> [--escribir]

Contrato:
  - Cada documento de Alejandría es un `.md` con `al:` y `resumen:` en el
    frontmatter. Sin esos dos campos, el documento no entra al catálogo y se
    reporta como huérfano — un documento sin resumen es ininvocable.
  - Los archivos que no son `.md` (datasets, CSV) viven junto a una ficha `.md`
    que sí los tiene. La ficha es lo que se cataloga.
  - `--escribir` sobrescribe `alejandria/INDICE.md`. Sin él, imprime a stdout.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

CHARS_POR_TOKEN = 4  # aproximación; ver vault_audit.py
CAMPOS = ("al", "titulo", "coleccion", "fecha", "estado", "origen", "resumen")
RE_FM = re.compile(r"\A---\r?\n(.*?)\r?\n---", re.DOTALL)


def frontmatter(texto: str) -> dict:
    m = RE_FM.match(texto)
    if not m:
        return {}
    datos = {}
    for linea in m.group(1).splitlines():
        if ":" in linea and not linea.startswith((" ", "\t", "-")):
            k, v = linea.split(":", 1)
            datos[k.strip()] = v.strip().strip('"')
    return datos


def recolectar(raiz: Path) -> tuple[list[dict], list[str]]:
    base = raiz / "alejandria"
    if not base.is_dir():
        sys.exit(f"ERROR: no existe {base}. Alejandría no está montada.")

    # Un listado por CARPETA, no por archivo. Antes se llamaba a
    # `p.parent.iterdir()` dentro del bucle: con 859 fichas y una colección de
    # 492, eran ~859 listados de directorio sobre drvfs, que es el sistema de
    # ficheros lento de este montaje. Medido el 2026-08-01: el paso dominaba la
    # certificación entera, y una compuerta que tarda minutos deja de correrse.
    no_md_por_dir: dict[Path, list[Path]] = {}

    def hermanos_de(carpeta: Path) -> list[Path]:
        if carpeta not in no_md_por_dir:
            no_md_por_dir[carpeta] = [
                q for q in carpeta.iterdir() if q.suffix != ".md" and q.is_file()
            ]
        return no_md_por_dir[carpeta]

    fichas, huerfanos = [], []
    for p in sorted(base.rglob("*.md")):
        # `INDICE.md` y los `INDICE_<COLECCION>.md` son catálogos GENERADOS, no
        # documentos: no llevan `al`/`resumen` y contarlos como huérfanos hacía
        # fallar la certificación por 10 archivos que el propio script escribe.
        if p.name.startswith("INDICE"):
            continue
        texto = p.read_text(encoding="utf-8", errors="replace")
        fm = frontmatter(texto)
        if "al" not in fm or "resumen" not in fm:
            huerfanos.append(str(p.relative_to(raiz)))
            continue
        # Peso real: la ficha más los datasets hermanos que describe.
        bytes_totales = p.stat().st_size
        hermanos = [
            q for q in hermanos_de(p.parent) if q.stem.startswith(fm["al"])
        ]
        bytes_totales += sum(q.stat().st_size for q in hermanos)
        fichas.append({
            **{c: fm.get(c, "") for c in CAMPOS},
            # Relativa a alejandria/, que es donde vive INDICE.md.
            "ruta": p.relative_to(base).as_posix(),
            "kb": bytes_totales / 1024,
            "tokens": len(texto) // CHARS_POR_TOKEN,
            "adjuntos": [q.name for q in hermanos],
        })

    # Sin `al` no hay orden estable: los IDs se asignan una vez y no se reusan.
    fichas.sort(key=lambda f: f["al"])
    # Counter en vez de recontar la lista entera por ficha (era O(n²): 859×859).
    duplicados = {al for al, n in Counter(f["al"] for f in fichas).items() if n > 1}
    if duplicados:
        sys.exit(f"ERROR: IDs duplicados en Alejandría: {sorted(duplicados)}. "
                 "Un ID identifica un documento y nunca se reasigna.")
    return fichas, huerfanos


def _slug_coleccion(nombre: str) -> str:
    """Nombre de archivo del sub-catálogo de una colección."""
    return "INDICE_" + re.sub(r"[^A-Za-z0-9_-]+", "-", nombre).strip("-").upper() + ".md"


def _tabla(docs: list[dict]) -> list[str]:
    L = ["| ID | Documento | Cuándo invocarlo | Coste | Estado |",
         "| --- | --- | --- | --- | --- |"]
    for f in docs:
        estado = "⚠️ sin verificar" if f["estado"] == "sin-verificar" else "✅"
        adj = f" +{len(f['adjuntos'])} adj." if f["adjuntos"] else ""
        L.append(
            f"| `{f['al']}` | [{f['titulo']}]({f['ruta'].replace(' ', '%20')}) | "
            f"{f['resumen']} | ~{f['tokens']:,} tok ({f['kb']:.0f} KB{adj}) | {estado} |"
        )
    return L + [""]


def render_coleccion(coleccion: str, docs: list[dict]) -> str:
    """Sub-catálogo de una colección: la tabla detallada, que solo se abre si hace falta."""
    tok = sum(f["tokens"] for f in docs)
    return "\n".join([
        "---", "tipo: catalogo", f"actualizado: {date.today().isoformat()}",
        "generado_por: vault-ops/scripts/alejandria_index.py", "---", "",
        f"# Alejandría — {coleccion}", "",
        f"**{len(docs)} documentos**, ~{tok:,} tokens si se abrieran todos.",
        "Volver a [[INDICE]]. **Este archivo no se edita a mano.**", "",
        *_tabla(docs),
    ])


def render(fichas: list[dict], huerfanos: list[str],
           colecciones: dict[str, list[dict]]) -> str:
    """Catálogo raíz: SOLO el mapa de colecciones.

    Antes era una tabla plana con una fila por documento. Con 40 documentos
    costaba ~1 000 tokens y el protocolo lo describía como barato; con 858 pasó a
    **77 417 tokens medidos el 2026-08-01** —8× el índice maestro— y "entrar por
    el catálogo" dejó de ser barato sin que nadie lo notara, porque nadie lo
    midió. El detalle baja a un sub-catálogo por colección, que es el mismo
    patrón de dos niveles que ya salva a `wiki/` vía `index.md`.
    """
    total_tokens = sum(f["tokens"] for f in fichas)

    L = [
        "---",
        "tipo: catalogo",
        f"actualizado: {date.today().isoformat()}",
        "generado_por: vault-ops/scripts/alejandria_index.py",
        "---",
        "",
        "# Alejandría — catálogo",
        "",
        "**Biblioteca de documentos extensos.** Lo que aquí vive vale por su texto",
        "completo, no solo por su síntesis: revisiones de investigación, informes",
        "largos, apuntes densos. Hermana de `wiki/` y `raw/`, no subordinada.",
        "",
        "> ⛔ **Nunca se carga entera.** Se entra por aquí, se elige **una**",
        "> colección, y de su sub-catálogo se abre **un** documento. Cargar",
        f"> Alejandría completa costaría ~{total_tokens:,} tokens.",
        "",
        "**Este archivo no se edita a mano.** Se regenera:",
        "`python3 /mnt/f/skills/_personales/vault-ops/scripts/alejandria_index.py /mnt/f/OBSIDIAN --escribir`",
        "",
        f"**{len(fichas)} documentos** en {len(colecciones)} colecciones, "
        f"~{total_tokens:,} tokens en total.",
        "",
        "| Colección | Docs | Si se abriera entera | Sub-catálogo |",
        "| --- | ---: | ---: | --- |",
    ]
    for coleccion, docs in sorted(colecciones.items(),
                                  key=lambda kv: -len(kv[1])):
        tok = sum(f["tokens"] for f in docs)
        L.append(f"| **{coleccion}** | {len(docs)} | ~{tok:,} tok | "
                 f"[{_slug_coleccion(coleccion)[:-3]}]({_slug_coleccion(coleccion)}) |")
    L.append("")

    if huerfanos:
        L += ["## ⚠️ Documentos sin catalogar", "",
              "Les falta `al:` o `resumen:` en el frontmatter. **Un documento sin",
              "resumen es ininvocable**: nadie puede decidir si abrirlo.", ""]
        L += [f"- `{h}`" for h in huerfanos] + [""]

    L += ["## Cómo entra un documento", "",
          "1. Llega a `raw/bandeja/` como todo lo demás.",
          "2. Se decide su destino: **síntesis** → nota en `wiki/`; **texto completo",
          "   que vale entero** → aquí; **capacidad reutilizable** → skill en",
          "   `F:\\skills\\_personales\\`. Los destinos no son excluyentes: un informe",
          "   puede dejar una nota sintética en `wiki/` y su texto íntegro aquí.",
          "3. Se le da un `AL-####` **nuevo y nunca reutilizado**, frontmatter con",
          "   `resumen` decisorio, y se regenera este catálogo en la misma operación.",
          ""]
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("raiz", type=Path)
    ap.add_argument("--escribir", action="store_true")
    args = ap.parse_args()

    raiz = args.raiz.resolve()
    fichas, huerfanos = recolectar(raiz)

    colecciones: dict[str, list[dict]] = {}
    for f in fichas:
        colecciones.setdefault(f["coleccion"] or "(sin colección)", []).append(f)

    salida = render(fichas, huerfanos, colecciones)

    if args.escribir:
        base = raiz / "alejandria"
        destino = base / "INDICE.md"
        destino.write_text(salida, encoding="utf-8")

        # Sub-catálogos por colección. Se limpian los de colecciones que ya no
        # existen: un catálogo que sobrevive a su contenido es peor que ninguno.
        vigentes = {_slug_coleccion(c) for c in colecciones}
        for viejo in base.glob("INDICE_*.md"):
            if viejo.name not in vigentes:
                viejo.unlink()
        for coleccion, docs in colecciones.items():
            (base / _slug_coleccion(coleccion)).write_text(
                render_coleccion(coleccion, docs), encoding="utf-8")

        raiz_tok = len(salida) // CHARS_POR_TOKEN
        print(f"catálogo -> {destino} ({len(fichas)} documentos, "
              f"{len(huerfanos)} sin catalogar)")
        print(f"  raíz: ~{raiz_tok:,} tokens · {len(colecciones)} sub-catálogos")
    else:
        print(salida)


if __name__ == "__main__":
    main()
