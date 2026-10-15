#!/usr/bin/env python3
"""Reporta adjuntos (imagenes, PDF, etc.) que ningun .md del vault referencia.

Solo reporta. Nunca borra ni mueve nada — coherente con la regla del vault de
que raw/ exige orden explicita y wiki/ no se borra, se marca. La version
original de este script (obsidian-templates de ykerus, cleanup-attachments.sh)
intentaba automatizar el borrado y tenia un bug real: `if $var > /dev/null`
no comprueba nada, intenta EJECUTAR el contenido de la variable como comando.

Uso:
    python3 adjuntos_huerfanos.py /mnt/f/OBSIDIAN
    python3 adjuntos_huerfanos.py /mnt/f/OBSIDIAN/raw/bandeja/notion --min-mb 0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

EXTENSIONES_ADJUNTO = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
    ".pdf", ".mp4", ".mp3", ".wav", ".zip",
}
EXCLUIR_DIRS = {".git", ".obsidian", "node_modules", "__pycache__"}


def iter_archivos(raiz: Path, extensiones: set[str] | None = None):
    for p in raiz.rglob("*"):
        if not p.is_file():
            continue
        if any(parte in EXCLUIR_DIRS for parte in p.parts):
            continue
        if extensiones is not None and p.suffix.lower() not in extensiones:
            continue
        yield p


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("carpeta_adjuntos", type=Path, help="Donde buscar adjuntos candidatos")
    ap.add_argument("--vault", type=Path, default=None, help="Raiz del vault donde buscar referencias (default: sube desde carpeta_adjuntos hasta encontrar CLAUDE.md, o usa carpeta_adjuntos)")
    ap.add_argument("--min-mb", type=float, default=0.0, help="Solo reportar adjuntos de al menos este tamano en MB")
    args = ap.parse_args()

    carpeta = args.carpeta_adjuntos.resolve()
    if not carpeta.is_dir():
        print(f"no existe: {carpeta}", file=sys.stderr)
        return 1

    vault = args.vault
    if vault is None:
        candidato = carpeta
        vault = carpeta
        for ancestro in carpeta.parents:
            if (ancestro / "CLAUDE.md").exists():
                vault = ancestro
                break
    vault = vault.resolve()

    print(f"adjuntos en: {carpeta}")
    print(f"buscando referencias en: {vault}\n")

    print("indexando texto de todas las notas .md del vault (una sola pasada)...")
    texto_vault = []
    for md in iter_archivos(vault, {".md"}):
        try:
            texto_vault.append(md.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
    corpus = "\n".join(texto_vault)
    print(f"  {len(texto_vault)} notas .md leidas, {len(corpus):,} caracteres\n")

    huerfanos = []
    revisados = 0
    for adjunto in iter_archivos(carpeta, EXTENSIONES_ADJUNTO):
        revisados += 1
        tam_mb = adjunto.stat().st_size / (1024 * 1024)
        if tam_mb < args.min_mb:
            continue
        if adjunto.name not in corpus:
            huerfanos.append((tam_mb, adjunto))

    huerfanos.sort(reverse=True)

    print(f"revisados: {revisados}")
    print(f"huerfanos (sin ninguna referencia por nombre en el vault): {len(huerfanos)}\n")
    if huerfanos:
        print(f"{'MB':>8}  ruta")
        for tam_mb, adjunto in huerfanos:
            print(f"{tam_mb:8.2f}  {adjunto.relative_to(vault) if adjunto.is_relative_to(vault) else adjunto}")
        total_mb = sum(t for t, _ in huerfanos)
        print(f"\ntotal huerfano: {total_mb:.1f} MB")
    print("\nEste script solo reporta. No borra ni mueve nada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
