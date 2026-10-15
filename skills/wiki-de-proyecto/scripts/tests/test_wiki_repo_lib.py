#!/usr/bin/env python3
"""La identidad de un artefacto publicado no son sus bytes.

⛔ **El defecto que esto cierra, medido el 2026-09-08.** El mismo canvas, en los
dos sitios donde vive:

| | `element/docs/wiki/` | `wiki/ELEMENT/APOLO/Mapas/` |
|---|---:|---:|
| bytes | 40 351 | **35 926** |
| líneas | 1 059 | **126** |
| sangría | 1 espacio (`json.dumps(indent=1)`) | **tabulador**, un nodo por línea |
| md5 | `86b9067223228b1b…` | `74fe55707a576f48…` |

Y sin embargo `json.load(a) == json.load(b)` es **True**: los mismos 65 nodos,
las mismas 56 aristas, las mismas claves. Obsidian no añadió nada — reescribió
el fichero al abrirlo, en su propio dialecto.

**Consecuencia de diseño, y es la que ordena todo el wiki repo:** cualquier
compuerta que compare `read_bytes()` contra la bóveda nace **roja permanente**, y
se dispararía cada vez que el usuario abre su propio mapa. Una compuerta que
grita por abrir un fichero es ruido, y el ruido se aprende a ignorar. Así que la
identidad de un artefacto es su **huella canónica**, no su serialización.

**Lo que la huella hace posible**, y que hoy es imposible: distinguir *quién*
movió el artefacto. Con una sola comparación (repo vs bóveda) sólo se sabe que
difieren. Con tres —repo, bóveda y la huella **adoptada** en el manifiesto— se
sabe si avanzó el generador, si lo editó el usuario a mano, o si avanzaron los
dos y hay conflicto. Esa tercera huella es el **índice de git**, y es la pieza
que faltaba.

Uso: python3 scripts/tests/test_wiki_repo_lib.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import wiki_repo_lib as W  # noqa: E402

#: Las dos copias reales del mismo mapa. Si no están montadas, ese caso se
#: declara no comprobado — nunca se cuenta como aprobado.
EN_REPO = Path("/home/kaitokid/Documents/REPOSITORIOS/element/docs/wiki/"
               "element_pipeline_nivelA.canvas")
EN_VAULT = Path("/mnt/f/OBSIDIAN/wiki/ELEMENT/APOLO/Mapas/"
                "01 — Pipeline completo del Nivel A.canvas")


def ok(titulo: str, condicion: bool, detalle: str = "") -> bool:
    print(f"  {'✓' if condicion else '✗'} {titulo}"
          + (f" → {detalle}" if detalle and not condicion else ""))
    return condicion


def caso_bytes_vs_huella() -> list[bool]:
    print("huella — Obsidian reescribe el fichero y el contenido no cambia")
    if not EN_REPO.is_file():
        print("  ⚠ el canvas real no está: caso NO comprobado")
        return []
    a = EN_REPO.read_text(encoding="utf-8")
    # El dialecto de Obsidian sobre el MISMO contenido. Se construye aquí en vez
    # de leer la copia de la bóveda porque publicar la re-normaliza: un test que
    # dependa del estado vivo del vault mide cuándo se publicó, no el fenómeno.
    b = json.dumps(json.loads(a), ensure_ascii=False, indent="\t")
    return [
        ok("los bytes SÍ difieren (si no, este test no prueba nada)", a != b,
           f"{len(a)} == {len(b)}"),
        ok("la huella canónica es la misma sobre 40 KB reales",
           W.huella_json(a) == W.huella_json(b),
           f"{W.huella_json(a)} vs {W.huella_json(b)}"),
    ]


def caso_huella_estable() -> list[bool]:
    print("\nhuella — no depende del orden de claves ni del espaciado")
    uno = '{"nodes": [{"id": "a", "x": 1}], "edges": []}'
    dos = '{\n\t"edges": [],\n\t"nodes": [\n\t\t{"x": 1, "id": "a"}\n\t]\n}'
    tres = '{"nodes": [{"id": "a", "x": 2}], "edges": []}'
    return [
        ok("mismo contenido, otra serialización → misma huella",
           W.huella_json(uno) == W.huella_json(dos)),
        ok("un valor distinto → otra huella",
           W.huella_json(uno) != W.huella_json(tres)),
        ok("un JSON roto no se hace pasar por válido",
           W.huella_json("{no soy json") is None),
    ]


def caso_quien_lo_movio() -> list[bool]:
    """La tabla de verdad. Cada lado se compara con SU propio punto de partida.

    El caso `adoptado` es el que hace honesto el sistema, y el que faltaba: tras
    adoptar una edición manual los dos ficheros difieren **a propósito**. Con una
    sola huella adoptada eso se leía como «avanzó el generador» y la siguiente
    corrida pisaba la edición del usuario — o sea, la compuerta habría protegido
    su trabajo exactamente una vez.
    """
    print("\nestado — con dos huellas adoptadas se sabe QUIÉN movió el artefacto")
    R, V = "repo", "vault"
    R2, V2 = "repo_nuevo", "vault_nuevo"
    return [
        ok("ausente en la bóveda → nuevo",
           W.situacion(R, None, R, None) == "nuevo"),
        ok("bóveda == repo → limpio",
           W.situacion(R, R, R, R) == "limpio"),
        ok("ninguno se movió y difieren → adoptado, y no se toca",
           W.situacion(R, V, R, V) == "adoptado"),
        ok("sólo se movió el repo → avanzó el generador",
           W.situacion(R2, V, R, V) == "generador_avanzo"),
        ok("sólo se movió la bóveda → lo editó el usuario",
           W.situacion(R, V2, R, V) == "editado_a_mano"),
        ok("se movieron los dos → conflicto",
           W.situacion(R2, V2, R, V) == "conflicto"),
        ok("sin lock y difieren → no se adivina quién fue",
           W.situacion(R, V) == "sin_adoptar"),
        ok("sin lock pero iguales → limpio igual",
           W.situacion(R, R) == "limpio"),
        ok("adoptar una edición manual NO la vuelve pisable en la corrida siguiente",
           not W.se_publica("generado", W.situacion(R, V, R, V))),
    ]


def caso_manual_no_se_pisa() -> list[bool]:
    print("\nprocedencia — un artefacto manual nunca se regenera")
    return [
        ok("`manual` no se sobrescribe ni cuando difiere",
           not W.se_publica("manual", "editado_a_mano")),
        ok("`manual` tampoco se sobrescribe estando limpio",
           not W.se_publica("manual", "limpio")),
        ok("`generado` sí se publica si es nuevo",
           W.se_publica("generado", "nuevo")),
        ok("`generado` se publica cuando avanzó el generador",
           W.se_publica("generado", "generador_avanzo")),
        ok("`generado` NO se pisa si lo editó el usuario",
           not W.se_publica("generado", "editado_a_mano")),
        ok("`generado` NO se pisa en conflicto",
           not W.se_publica("generado", "conflicto")),
        ok("`generado` NO se pisa si la diferencia está adoptada",
           not W.se_publica("generado", "adoptado")),
        ok("una procedencia desconocida no se publica por defecto",
           not W.se_publica("loquesea", "nuevo")),
    ]


def main() -> int:
    r = (caso_bytes_vs_huella() + caso_huella_estable()
         + caso_quien_lo_movio() + caso_manual_no_se_pisa())
    print(f"\n{sum(r)}/{len(r)} verde")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
