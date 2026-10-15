#!/usr/bin/env python3
"""Da de alta en Alejandría los candidatos que `triaje.py` marcó como
ALEJANDRIA en `raw/_triaje_estado.json`, asignando ID permanente + colección
por palabra clave. Mecánico, no evalúa si el contenido es correcto — esa
decisión sigue siendo del usuario, en su proyecto.

Uso:
    python alejandria_intake.py <raiz_vault>              # dry-run, muestra el plan
    python alejandria_intake.py <raiz_vault> --aplicar     # mueve y escribe frontmatter
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

REGLAS = [
    ("ACIDITHIOBACILLUS", [
        "acidithiobacillus", "bioleaching", "ferrooxidans", "thiobacillus",
        "grafito", "lodos de relave", "graphite", "electrochemical",
        "bacterial metal", "cu bioleaching", "e-wastes",
    ]),
    ("EMPRESA", [
        "sapyria", "minuta", "constitucion", "contrato", "sunarp", "regulatorio",
        "modelo de negocio", "viabilidad", "marketing", "centricidad",
        "plantillas de modelo", "night deeptech", "limitacion contractual",
        "platafroma",
    ]),
    ("SHEWANELLA", [
        "pwy", "pathway", "gem", "metabolic", "metabolico", "rutas metabolicas",
        "pcr", "fucosa", "bitacora", "shewanella", "decoloracion",
        "estequiometric", "lc6", "esquematico", "geppy", "modelamiento",
        "igem", "colorante", "azoreductas", "cinetica",
    ]),
]
DEFAULT_COLECCION = "VARIOS"

RAIZ_ESPERADA_ID = re.compile(r"^AL-(\d+)$")
RE_FM = re.compile(r"\A---\r?\n(.*?)\r?\n---", re.DOTALL)


def slugify(nombre: str) -> str:
    nombre = re.sub(r"-[0-9a-f]{32}$", "", nombre)  # hash de Notion
    nombre = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    nombre = re.sub(r"[^a-zA-Z0-9]+", "-", nombre).strip("-").lower()
    return nombre[:60] or "documento"


def clasificar(ruta: str) -> str:
    r = unicodedata.normalize("NFKD", ruta.lower()).encode("ascii", "ignore").decode()
    for coleccion, claves in REGLAS:
        if any(c in r for c in claves):
            return coleccion
    return DEFAULT_COLECCION


def siguiente_id(base: Path) -> int:
    maximo = 0
    for p in base.rglob("*.md"):
        if p.name == "INDICE.md":
            continue
        m = RE_FM.match(p.read_text(encoding="utf-8", errors="replace"))
        if not m:
            continue
        for linea in m.group(1).splitlines():
            if linea.startswith("al:"):
                mm = RAIZ_ESPERADA_ID.match(linea.split(":", 1)[1].strip())
                if mm:
                    maximo = max(maximo, int(mm.group(1)))
    return maximo + 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("raiz", type=Path)
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    raiz = args.raiz.resolve()
    estado_path = raiz / "raw" / "_triaje_estado.json"
    estado = json.loads(estado_path.read_text(encoding="utf-8"))
    candidatos = sorted(
        (ruta, dec) for ruta, dec in estado["decisiones"].items()
        if dec["destino"] == "ALEJANDRIA"
    )

    siguiente = siguiente_id(raiz / "alejandria")
    print(f"{len(candidatos)} candidatos. Próximo ID libre: AL-{siguiente:04d}\n")

    fecha_hoy = "2026-07-30"
    plan = []
    for ruta, dec in candidatos:
        src = raiz / ruta
        if not src.is_file():
            print(f"  [saltado, no existe] {ruta}")
            continue
        coleccion = clasificar(ruta)
        titulo_bruto = Path(ruta).stem
        titulo_bruto = re.sub(r"-[0-9a-f]{32}$", "", titulo_bruto)
        al_id = f"AL-{siguiente:04d}"
        slug = slugify(Path(ruta).stem)
        destino = raiz / "alejandria" / coleccion / f"{al_id}_{slug}.md"
        plan.append((src, destino, al_id, coleccion, titulo_bruto, dec))
        siguiente += 1

    for src, destino, al_id, coleccion, titulo, dec in plan:
        print(f"  {al_id}  [{coleccion:16s}]  {destino.relative_to(raiz / 'alejandria')}")

    if not args.aplicar:
        print("\nDry-run. Volvé a correr con --aplicar para mover y escribir frontmatter.")
        return

    for src, destino, al_id, coleccion, titulo, dec in plan:
        destino.parent.mkdir(parents=True, exist_ok=True)
        cuerpo = src.read_text(encoding="utf-8", errors="replace")
        resumen = dec.get("resumen", "").replace('"', "'")
        origen = (
            f"Notion export (raw/bandeja/{Path(src).relative_to(raiz / 'raw' / 'bandeja')}); "
            f"clasificado ALEJANDRIA por triaje.py (modelo local, 2026-07-29), "
            f"enrutado a colección '{coleccion}' por palabra clave el {fecha_hoy} — "
            f"revisar si la colección asignada es correcta."
        )
        frontmatter = (
            "---\n"
            f"al: {al_id}\n"
            f"titulo: \"{titulo}\"\n"
            f"coleccion: {coleccion}\n"
            f"fecha: {fecha_hoy}\n"
            "estado: sin-verificar\n"
            f"origen: \"{origen}\"\n"
            f"resumen: \"{resumen}\"\n"
            "---\n\n"
        )
        destino.write_text(frontmatter + cuerpo, encoding="utf-8")
        src.unlink()

    print(f"\n{len(plan)} documentos dados de alta en Alejandría.")
    print("Corré alejandria_index.py --escribir para regenerar el catálogo.")


if __name__ == "__main__":
    main()
