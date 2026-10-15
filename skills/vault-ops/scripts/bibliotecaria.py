#!/usr/bin/env python3
"""Bibliotecaria: EXTRAE (no sintetiza) sobre los candidatos a wiki que
`triaje.py` dejó en CANDIDATA_WIKI. Genera borradores en `raw/_borradores_wiki/`
con citas ancladas al documento fuente — nunca escribe en `wiki/` directamente.

## Por qué esto y no "que el 9B redacte la nota"

Medido (ver `wiki/SISTEMA/Amadeus — el segundo cerebro como backend.md`): un 9B
clasifica bien y sintetiza mal — juzgar qué es cierto en un documento entero
excede lo que puede sostener sin alucinar. Pero EXTRAER texto que ya está ahí es
el mismo tipo de tarea barata donde `triaje.py` sí funcionó.

La apuesta se verifica, no se asume: cada `cita` que el modelo devuelve se
compara contra el texto fuente (normalizando espacios). Lo que no aparece
literal se descarta de la cita y queda contado como "alucinada". El borrador
completo lleva ese conteo en el frontmatter — la compuerta de promoción a
`wiki/` (humana, o de un modelo mayor) puede exigir 0 alucinadas antes de
confiar en un borrador.

## Orden de la cola (2026-07-30)

Prioridad: (0) capturado manualmente por el usuario (bookmarklet u otra
captura a mano) → (1) lo que ya estaba en la bandeja antes de la ingesta
automatizada, sin reordenar → (2) traído por un scraper automatizado
(twitter/arxiv/biorxiv/reddit). El volumen de ingesta automatizada no debe
postergar lo que un humano priorizó a mano.

Uso:
    python bibliotecaria.py --n 5              # prototipo, 5 candidatos
    python bibliotecaria.py --n 0              # todos los CANDIDATA_WIKI pendientes
    python bibliotecaria.py --informe          # resumen de lo generado
"""
from __future__ import annotations

import argparse
import json
import re
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path("/mnt/f/OBSIDIAN")
BORRADORES = RAIZ / "raw" / "_borradores_wiki"
ESTADO_TRIAJE = RAIZ / "raw" / "_triaje_estado.json"
ESTADO = RAIZ / "raw" / "_bibliotecaria_estado.json"
OLLAMA = "http://127.0.0.1:11434/api/generate"
MODELO = "qwen3.5:9b"
PERSONA = Path("/mnt/f/skills/_personales/vault-ops/amadeus/PERSONA_BIBLIOTECARIA.md")


def normalizar(s: str) -> str:
    s = unicodedata.normalize("NFKC", s.lower())
    return re.sub(r"\s+", " ", s).strip()


# Orígenes que llegan por scraping automatizado — se procesan último. Pedido
# explícito del usuario (2026-07-30): que el volumen de ingesta automatizada
# no postergue lo que un humano puso a mano en la bandeja.
_ORIGENES_SCRAPER = ("twitter", "arxiv", "biorxiv", "reddit")


def _prioridad(ruta: str) -> int:
    """0 = capturado manualmente (máxima prioridad) · 1 = lo que ya estaba en
    la bandeja antes de la ingesta automatizada (prioridad normal, sin
    cambios) · 2 = traído por un scraper (se procesa al final). Se decide
    mirando el frontmatter, no adivinando por la ruta."""
    try:
        inicio = (RAIZ / ruta).read_text(encoding="utf-8", errors="replace")[:600]
    except OSError:
        return 1
    if "capturado_via" in inicio and "manual" in inicio:
        return 0
    if any(f"origen: {o}" in inicio for o in _ORIGENES_SCRAPER):
        return 2
    return 1


def candidatos_pendientes() -> list[str]:
    triaje = json.loads(ESTADO_TRIAJE.read_text(encoding="utf-8"))
    hechos = cargar_estado()["hechas"]
    rutas = [
        ruta for ruta, dec in triaje["decisiones"].items()
        if dec["destino"] == "CANDIDATA_WIKI" and ruta not in hechos
    ]
    return sorted(rutas, key=lambda r: (_prioridad(r), r))


def cargar_estado() -> dict:
    if ESTADO.is_file():
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    return {"hechas": {}}


def guardar_estado(e: dict) -> None:
    ESTADO.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")


def extraer(texto_fuente: str, nombre: str, reintentos: int = 2) -> dict | None:
    # 600 tokens truncaba la salida a mitad de un string JSON en documentos
    # normales (medido 2026-08-05: reacciones.md necesitó 1146, done_reason
    # "length" en el 100% de los 61 fallos "sin JSON válido" de la corrida del
    # 31-jul). Arranca con margen y dobla si el corte fue por longitud, no por
    # error de red — reintentar con el mismo tope solo repite el mismo corte.
    num_predict = 1400
    prompt = (
        PERSONA.read_text(encoding="utf-8") +
        f"\n\n## Documento a procesar (nombre: {nombre})\n\n{texto_fuente}\n\n"
        "Respondé SOLO el JSON pedido, nada de texto antes o después."
    )

    for intento in range(reintentos):
        cuerpo = json.dumps({
            "model": MODELO, "prompt": prompt, "stream": False,
            "think": False, "format": "json",
            "options": {"temperature": 0, "num_predict": num_predict},
        }).encode()
        d: dict = {}
        try:
            req = urllib.request.Request(OLLAMA, data=cuerpo,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                d = json.loads(resp.read())
            out = json.loads(d.get("response", "") or "{}")
            if isinstance(out.get("citas"), list):
                return out
        except json.JSONDecodeError:
            if d.get("done_reason") == "length":
                num_predict = min(num_predict * 2, 4000)
        except (urllib.error.URLError, ValueError, TypeError):
            pass
        time.sleep(0.5 * (intento + 1))
    return None


def verificar_citas(citas: list, fuente_norm: str) -> tuple[list[str], list[str]]:
    """Devuelve (citas_ancladas, citas_alucinadas). Ancla = substring literal
    del documento fuente, normalizando mayúsculas/espacios pero NADA más —
    si el modelo parafraseó aunque sea un poco, se cuenta como alucinada."""
    ancladas, alucinadas = [], []
    for c in citas:
        if not isinstance(c, str) or not c.strip():
            continue
        if normalizar(c) in fuente_norm:
            ancladas.append(c.strip())
        else:
            alucinadas.append(c.strip())
    return ancladas, alucinadas


def procesar(n: int) -> None:
    cola = candidatos_pendientes()
    if n > 0:
        cola = cola[:n]
    if not cola:
        print("No quedan candidatos pendientes.")
        return

    BORRADORES.mkdir(parents=True, exist_ok=True)
    estado = cargar_estado()
    t0 = time.time()
    ok, con_alucinacion, fallidos = 0, 0, 0

    for i, ruta in enumerate(cola, 1):
        src = RAIZ / ruta
        if not src.is_file():
            estado["hechas"][ruta] = {"resultado": "fuente_ausente"}
            continue
        texto = src.read_text(encoding="utf-8", errors="replace")
        cuerpo = re.sub(r"\A﻿?---\r?\n.*?\r?\n---\r?\n", "", texto, flags=re.DOTALL)
        out = extraer(cuerpo, src.stem)
        if out is None:
            fallidos += 1
            print(f"  [{i}/{len(cola)}] FALLÓ (sin JSON válido): {ruta}")
            continue

        fuente_norm = normalizar(cuerpo)
        ancladas, alucinadas = verificar_citas(out.get("citas", []), fuente_norm)
        encabezados_ancl, encabezados_aluc = verificar_citas(
            out.get("encabezados", []), fuente_norm)

        slug = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize(
            "NFKD", src.stem.lower()).encode("ascii", "ignore").decode()).strip("-")[:60]
        destino = BORRADORES / f"{slug or 'documento'}.md"

        total_citas = len(ancladas) + len(alucinadas)
        frontmatter = (
            "---\n"
            "borrador: true\n"
            "estado: sin-verificar\n"
            "generado_por: bibliotecaria (qwen3.5:9b, extracción, no síntesis)\n"
            f"fuente: \"{ruta}\"\n"
            f"titulo_propuesto: \"{str(out.get('titulo_propuesto',''))[:150]}\"\n"
            f"citas_ancladas: {len(ancladas)}\n"
            f"citas_alucinadas: {len(alucinadas)}\n"
            f"encabezados_alucinados: {len(encabezados_aluc)}\n"
            "---\n\n"
        )
        cuerpo_md = [
            f"# {out.get('titulo_propuesto','(sin título propuesto)')}\n",
            "## Resumen (borrador, del modelo local — no verificado)\n",
            f"{out.get('resumen_borrador','')}\n",
            "## Encabezados detectados en la fuente\n",
        ]
        cuerpo_md += [f"- {h}" for h in encabezados_ancl] or ["(ninguno anclado)"]
        cuerpo_md.append("\n## Citas textuales (verificadas contra la fuente)\n")
        cuerpo_md += [f"> {c}" for c in ancladas] or ["(ninguna anclada)"]
        if alucinadas:
            cuerpo_md.append("\n## ⚠️ Citas que el modelo propuso y NO aparecen en la fuente (descartadas)\n")
            cuerpo_md += [f"- ~~{c}~~" for c in alucinadas]

        destino.write_text(frontmatter + "\n".join(cuerpo_md) + "\n", encoding="utf-8")

        estado["hechas"][ruta] = {
            "resultado": "ok", "borrador": str(destino.relative_to(RAIZ)),
            "citas_ancladas": len(ancladas), "citas_alucinadas": len(alucinadas),
        }
        if alucinadas or encabezados_aluc:
            con_alucinacion += 1
        else:
            ok += 1
        print(f"  [{i}/{len(cola)}] {ruta}  ->  {len(ancladas)} citas ancladas, "
              f"{len(alucinadas)} alucinadas")

        if i % 10 == 0 or i == len(cola):
            guardar_estado(estado)

    guardar_estado(estado)
    print(f"\nlimpios: {ok} | con alguna alucinación descartada: {con_alucinacion} | "
          f"fallidos: {fallidos} | tiempo: {time.time()-t0:.0f}s")
    print(f"Borradores en: {BORRADORES.relative_to(RAIZ)}")


def informe() -> None:
    estado = cargar_estado()
    h = estado["hechas"]
    if not h:
        print("Nada generado todavía.")
        return
    ok = [v for v in h.values() if v.get("resultado") == "ok"]
    total_citas = sum(v.get("citas_ancladas", 0) for v in ok)
    total_aluc = sum(v.get("citas_alucinadas", 0) for v in ok)
    limpios = sum(1 for v in ok if v.get("citas_alucinadas", 0) == 0)
    print(f"# Bibliotecaria — {len(h)} procesados\n")
    print(f"- borradores generados: {len(ok)}")
    print(f"- sin ninguna cita alucinada: {limpios}/{len(ok)}")
    print(f"- citas ancladas totales: {total_citas}")
    print(f"- citas alucinadas totales (descartadas): {total_aluc}")
    if total_citas + total_aluc:
        print(f"- tasa de alucinación: {100*total_aluc/(total_citas+total_aluc):.1f}%")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--informe", action="store_true")
    args = ap.parse_args()
    if args.informe:
        informe()
    else:
        procesar(args.n)


if __name__ == "__main__":
    main()
