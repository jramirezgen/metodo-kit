#!/usr/bin/env python3
"""
esquema_areas.py — inyecta el esquema Área/Tema en el frontmatter de wiki/.

Replica el modelo relacional del Notion "KaiToKid Dashboard" (Área → Tema →
Notas) SIN reproducir su error: allí las Áreas y los Temas eran páginas cuyo
único contenido era un índice de otras páginas, y casi todas estaban vacías
(28 Temas recuperados el 2026-07-30, la mayoría con `0 Notes`).

Aquí `area` y `tema` son PROPIEDADES, no archivos. Las páginas de Área se
rellenan solas con Dataview; ninguna nota se crea vacía.

Ambos campos son listas: una nota puede pertenecer a varias Áreas (la
economía de Sapyria es Empresa *y* Finanzas) igual que en Notion una Nota
enlazaba varios Temas.

Uso:
    python3 esquema_areas.py <VAULT> [--aplicar]   # sin --aplicar: simulacro
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ── Vocabulario controlado de Áreas ───────────────────────────────────────
# Las 7 que el usuario nombró + Empresa y Sistema, que el vault ya tenía
# con contenido real (13 y 26 notas) y necesitaban Área para no quedar fuera.
AREAS = [
    "Investigación", "Empresa", "Sistema", "Conocimiento",
    "Relaciones", "Clientes", "Finanzas", "Salud", "Talleres",
]

# ── Reglas por carpeta: (prefijo de ruta) -> (áreas, temas) ───────────────
# Se evalúan de la más específica a la más general.
POR_CARPETA: list[tuple[str, list[str], list[str]]] = [
    ("PRINCIPIA/Tomos/",        ["Investigación"], ["Principia"]),
    ("PRINCIPIA/",              ["Investigación"], ["Teoría TGDE"]),
    ("ELEMENT/",                ["Investigación"], ["Motor ELEMENT"]),
    ("SHEWANELLA/",             ["Investigación"], ["Shewanella LC6"]),
    ("HAMCAO/Bitácora/",        ["Investigación"], ["HAMCAO", "Bitácora"]),
    ("HAMCAO/Fucosa_Sulfatada/",["Investigación"], ["HAMCAO", "Fucosa Sulfatada"]),
    ("HAMCAO/Vinaza/",          ["Investigación"], ["HAMCAO", "Vinaza"]),
    ("HAMCAO/",                 ["Investigación"], ["HAMCAO"]),
    ("ECOLI/",                  ["Investigación"], ["E. coli K-12"]),
    ("EMPRESA/",                ["Empresa"],       []),
    ("SISTEMA/",                ["Sistema"],       []),
]

# ── Excepciones por nota ──────────────────────────────────────────────────
# Solo donde la carpeta no basta: notas que cruzan Área o que necesitan Tema
# propio. Clave = nombre de archivo sin `.md`.
POR_NOTA: dict[str, tuple[list[str], list[str]]] = {
    # EMPRESA — se abre en las líneas de negocio reales
    "Sapyria":                                  (["Empresa"], ["Sapyria"]),
    "Economía Unitaria Sapyria":                (["Empresa", "Finanzas"], ["Sapyria"]),
    "Mapa Competitivo de Lima":                 (["Empresa", "Clientes"], ["Sapyria", "Mercado"]),
    "Marco Regulatorio Sanitario Sapyria":      (["Empresa"], ["Sapyria", "Leyes"]),
    "Riesgo Legal del Diagnóstico Genético":    (["Empresa"], ["Sapyria", "Leyes"]),
    "Blindaje Contractual frente a Terceros":   (["Empresa", "Clientes"], ["Leyes"]),
    "Constitución Societaria Sapyria":          (["Empresa"], ["Sapyria", "Leyes"]),
    "AgroGlim":                                 (["Empresa"], ["AgroGlim"]),
    "Bioensayo de Fucosa como Bioestimulante":  (["Empresa", "Investigación"], ["AgroGlim"]),
    "Biomined":                                 (["Empresa"], ["Biomined"]),
    "Regulador Maestro de Electroautotrofía":   (["Empresa", "Investigación"], ["Biomined"]),
    "CIMMA":                                    (["Empresa", "Relaciones"], ["CIMMA"]),
    "Método 404 Tech Found":                    (["Empresa"], ["Método 404"]),

    # SISTEMA — se separa el vault, los agentes, las skills y la evidencia
    "Alejandría (biblioteca de documentos extensos)":            (["Sistema"], ["Vault"]),
    "Auditoría de Calidad del Vault (2026-07-28)":               (["Sistema"], ["Vault"]),
    "Auditoría del Vault II (2026-07-28, post-intervención)":    (["Sistema"], ["Vault"]),
    "Autoridad Epistémica Local":                                (["Sistema"], ["Vault"]),
    "Cifras Canónicas":                                          (["Sistema"], ["Vault"]),
    "Graphify sobre el Vault":                                   (["Sistema"], ["Vault"]),
    "vault-ops (medición del segundo cerebro)":                  (["Sistema"], ["Vault", "Skills"]),
    "Cerebro Notion":                                            (["Sistema"], ["Vault", "Notion"]),
    "Infraestructura evaluada — qué se instala y qué no (2026-07-28)": (["Sistema"], ["Vault"]),
    "Agnes - Agente Local":                                      (["Sistema"], ["Amadeus"]),
    "Amadeus - Stack LLM Autónomo":                              (["Sistema"], ["Amadeus"]),
    "Amadeus — el segundo cerebro como backend":                 (["Sistema"], ["Amadeus", "Vault"]),
    "Arquitectura de Skills en 3 Capas":                         (["Sistema"], ["Skills"]),
    "Biblioteca F-skills (catálogo externo)":                    (["Sistema"], ["Skills"]),
    "Biblioteca de Skills Técnicas (Claude Code)":               (["Sistema"], ["Skills"]),
    "Generador P&ID Data-Driven (ISA-5.1)":                      (["Sistema"], ["Skills"]),
    "Filosofía Pragmática en ELEMENT (8.7-10)":                  (["Sistema"], ["Skills"]),
    "Gemelo Digital Empresarial (plantilla)":                    (["Sistema", "Empresa"], ["Skills"]),
    "Mapa de Proyectos":                                         (["Sistema"], ["Proyectos"]),
    "Mapa de Repositorios":                                      (["Sistema"], ["Proyectos"]),
    "Notebooks Reproducibles (dónde vive la evidencia)":         (["Sistema", "Investigación"], ["Evidencia"]),
    "PioReactor Modificado":                                     (["Sistema", "Investigación"], ["Biomined", "Hardware"]),
    "Vigilancia de Federación de Datos":                         (["Sistema"], ["Datos"]),

    # Las dos notas que ya vivían fuera de su Área natural
    "Corpus de Referencias":                                     (["Conocimiento"], ["Referencias"]),
    "Escalera de Habilidades":                                   (["Talleres"], ["Formación"]),
}

RE_FM = re.compile(r"\A(﻿?)---\r?\n(.*?)\r?\n---", re.S)


def _yaml_lista(clave: str, valores: list[str]) -> str:
    return f"{clave}: [" + ", ".join(valores) + "]"


def clasificar(rel: str) -> tuple[list[str], list[str]] | None:
    nombre = Path(rel).stem
    if nombre in POR_NOTA:
        return POR_NOTA[nombre]
    for prefijo, areas, temas in POR_CARPETA:
        if rel.startswith(prefijo):
            if not temas:
                return None  # carpeta que exige excepción explícita
            return areas, temas
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("vault", type=Path)
    ap.add_argument("--aplicar", action="store_true")
    a = ap.parse_args()

    wiki = a.vault / "wiki"
    hechas, saltadas, sin_regla = 0, 0, []

    for md in sorted(wiki.rglob("*.md")):
        rel = str(md.relative_to(wiki)).replace("\\", "/")
        clas = clasificar(rel)
        if clas is None:
            sin_regla.append(rel)
            continue
        areas, temas = clas
        malas = [x for x in areas if x not in AREAS]
        if malas:
            print(f"✗ área fuera del vocabulario en {rel}: {malas}")
            return 1

        txt = md.read_text(encoding="utf-8")
        m = RE_FM.match(txt)
        if not m:
            print(f"✗ sin frontmatter: {rel}")
            return 1
        bom, fm = m.group(1), m.group(2)
        if re.search(r"^area:", fm, re.M):
            saltadas += 1
            continue

        lineas = fm.split("\n")
        # se inserta justo después de `tags:`, que todas las notas ya tienen
        idx = next((i for i, l in enumerate(lineas) if l.startswith("tags:")), -1)
        nuevas = [_yaml_lista("area", areas), _yaml_lista("tema", temas)]
        lineas[idx + 1: idx + 1] = nuevas

        if a.aplicar:
            md.write_text(f"{bom}---\n" + "\n".join(lineas) + "\n---" + txt[m.end():],
                          encoding="utf-8")
        hechas += 1
        print(f"{'✓' if a.aplicar else '·'} {rel:70} area={areas} tema={temas}")

    print(f"\n{'APLICADO' if a.aplicar else 'SIMULACRO'} — "
          f"{hechas} notas, {saltadas} ya tenían `area`, {len(sin_regla)} sin regla")
    for r in sin_regla:
        print(f"  ⚠️ sin regla: {r}")
    return 1 if sin_regla else 0


if __name__ == "__main__":
    sys.exit(main())
