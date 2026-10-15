#!/usr/bin/env python3
"""Genera fichas de sugerencia de proyecto a partir de papers/posts ya
capturados en `raw/bandeja/papers/` y `raw/bandeja/reddit/` — un paso
ADICIONAL al pipeline `triaje.py`/`bibliotecaria.py`, no un reemplazo.

## Por qué esto es DISTINTO de bibliotecaria.py, a propósito

`bibliotecaria.py` extrae CITAS ANCLADAS — verificables mecánicamente como
substring literal del documento fuente. Lo que se pide acá es otra cosa: una
opinión sobre si un paper/post podría ser relevante para investigación
propia. Eso es, por naturaleza, una ESPECULACIÓN, no un hecho verificable —
no hay compuerta anti-alucinación posible sobre una opinión. La honestidad
acá se sostiene de otra forma: etiquetado explícito ("especulativo, no
verificado") + la compuerta real, que es la aprobación humana. El modelo
propone; nada se promueve solo.

Cada ficha sale con `estado_aprobacion: "[ ] Pendiente de aprobación"` — no
es una automatización de decisiones, es un tablón para que el usuario decida.

Reusa la clasificación de `triaje.py`: si un paper/post ya fue marcado RUIDO,
no genera ficha (no tiene sentido especular sobre algo sin contenido útil).

Uso:
    python sugerencias.py --n 10        # prueba
    python sugerencias.py --n 0         # todos los pendientes
    python sugerencias.py --informe
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
FUENTES = [RAIZ / "raw" / "bandeja" / "papers", RAIZ / "raw" / "bandeja" / "reddit"]
DESTINO = RAIZ / "raw" / "bandeja" / "sugerencias_proyectos"
ESTADO_TRIAJE = RAIZ / "raw" / "_triaje_estado.json"
ESTADO = RAIZ / "raw" / "_sugerencias_estado.json"
OLLAMA = "http://127.0.0.1:11434/api/generate"
MODELO = "qwen3.5:9b"

RE_FM = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n(.*)", re.DOTALL)


def frontmatter_y_cuerpo(texto: str) -> tuple[dict, str]:
    m = RE_FM.match(texto)
    if not m:
        return {}, texto
    fm = {}
    for linea in m.group(1).splitlines():
        if ":" in linea:
            k, v = linea.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm, m.group(2)


def cargar_estado() -> dict:
    if ESTADO.is_file():
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    return {"hechas": {}}


def guardar_estado(e: dict) -> None:
    ESTADO.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")


def clasificacion_triaje() -> dict:
    if not ESTADO_TRIAJE.is_file():
        return {}
    return json.loads(ESTADO_TRIAJE.read_text(encoding="utf-8")).get("decisiones", {})


def slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()[:60]


def pendientes(estado: dict, decisiones_triaje: dict) -> list[Path]:
    hechas = estado["hechas"]
    resultado = []
    for base in FUENTES:
        for p in sorted(base.rglob("*.md")):
            ruta_rel = str(p.relative_to(RAIZ))
            if ruta_rel in hechas:
                continue
            destino_triaje = decisiones_triaje.get(ruta_rel, {}).get("destino")
            if destino_triaje == "RUIDO":
                continue  # sin contenido útil, no tiene sentido especular
            resultado.append(p)
    return resultado


def preguntar(fm: dict, cuerpo: str, reintentos: int = 2) -> dict | None:
    contexto_termino = fm.get("termino_coincidente") or fm.get("subreddit", "")
    prompt = (
        "Evalúas papers/posts capturados para un pipeline de investigación en "
        "bioinformática/biología de sistemas/modelado metabólico. Respondés "
        "SIEMPRE JSON válido y nada más.\n\n"
        f"Título: {fm.get('titulo', '')}\n"
        f"Fuente: {fm.get('origen', '')} (coincidió con: {contexto_termino})\n"
        f"Contenido:\n{cuerpo[:2000]}\n\n"
        "Devolvé JSON con claves exactas:\n"
        "- resumen: 1-2 frases sobre qué ES este paper/post, basado SOLO en el "
        "texto de arriba, sin agregar datos que no estén ahí.\n"
        "- potencial_aplicacion: 1-2 frases sobre por qué podría ser relevante "
        "para investigación en bioinformática/modelado metabólico. Frasealo "
        "EXPLÍCITAMENTE como especulación (\"podría ser relevante para...\", "
        "\"si aplica...\"), nunca como una afirmación de hecho."
    )
    cuerpo_req = json.dumps({
        "model": MODELO, "prompt": prompt, "stream": False,
        "think": False, "format": "json",
        "options": {"temperature": 0, "num_predict": 300},
    }).encode()

    for intento in range(reintentos):
        try:
            req = urllib.request.Request(OLLAMA, data=cuerpo_req,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                d = json.loads(resp.read())
            out = json.loads(d.get("response", "") or "{}")
            if out.get("resumen") and out.get("potencial_aplicacion"):
                return out
        except (urllib.error.URLError, json.JSONDecodeError, ValueError, TypeError):
            pass
        time.sleep(0.5 * (intento + 1))
    return None


def escribir_ficha(p: Path, fm: dict, out: dict) -> Path:
    tipo = "reddit" if "reddit" in fm.get("origen", "") else "paper"
    titulo = fm.get("titulo", p.stem)
    nombre = f"sugerencia_{slug(titulo)}.md"
    destino = DESTINO / nombre
    frontmatter = (
        "---\n"
        f"origen_fuente: \"{p.relative_to(RAIZ)}\"\n"
        f"tipo: {tipo}\n"
        f"titulo: \"{titulo[:200]}\"\n"
        f"url: \"{fm.get('url', '')}\"\n"
        "estado_aprobacion: \"[ ] Pendiente de aprobación\"\n"
        "generado_por: \"sugerencias.py (qwen3.5:9b) — especulativo, no verificado\"\n"
        f"fecha: \"{time.strftime('%Y-%m-%d')}\"\n"
        "---\n\n"
    )
    cuerpo_md = (
        f"# Sugerencia: {titulo}\n\n"
        f"**Fuente:** [{fm.get('origen', '')}]({fm.get('url', '')})\n\n"
        "## Resumen del descubrimiento\n\n"
        f"{out['resumen']}\n\n"
        "## Potencial de aplicación (especulativo — revisar antes de actuar)\n\n"
        f"{out['potencial_aplicacion']}\n\n"
        "## Aprobación\n\n"
        "- [ ] Pendiente de aprobación\n"
    )
    DESTINO.mkdir(parents=True, exist_ok=True)
    destino.write_text(frontmatter + cuerpo_md, encoding="utf-8")
    return destino


def procesar(n: int) -> None:
    estado = cargar_estado()
    decisiones_triaje = clasificacion_triaje()
    cola = pendientes(estado, decisiones_triaje)
    if n > 0:
        cola = cola[:n]
    if not cola:
        print("No quedan archivos pendientes (o todo lo pendiente es RUIDO).")
        return

    print(f"Generando sugerencias para {len(cola)} archivos con {MODELO} (local)…")
    t0, ok, fallidos = time.time(), 0, 0
    for i, p in enumerate(cola, 1):
        texto = p.read_text(encoding="utf-8", errors="replace")
        fm, cuerpo = frontmatter_y_cuerpo(texto)
        out = preguntar(fm, cuerpo)
        if out is None:
            fallidos += 1
            print(f"  [{i}/{len(cola)}] FALLÓ (sin JSON válido): {p.name}")
            continue
        destino = escribir_ficha(p, fm, out)
        estado["hechas"][str(p.relative_to(RAIZ))] = {"ficha": str(destino.relative_to(RAIZ))}
        ok += 1
        print(f"  [{i}/{len(cola)}] {p.name} -> {destino.name}")
        if i % 10 == 0 or i == len(cola):
            guardar_estado(estado)

    guardar_estado(estado)
    print(f"\n{ok} fichas generadas, {fallidos} fallidas, {time.time()-t0:.0f}s")
    print(f"Revisar en: raw/bandeja/sugerencias_proyectos/")


def informe() -> None:
    estado = cargar_estado()
    print(f"# Sugerencias — {len(estado['hechas'])} fichas generadas")
    pendientes_aprobacion = 0
    for info in estado["hechas"].values():
        ficha = RAIZ / info["ficha"]
        if ficha.is_file() and "[ ] Pendiente" in ficha.read_text(encoding="utf-8"):
            pendientes_aprobacion += 1
    print(f"- pendientes de aprobación: {pendientes_aprobacion}")
    print(f"- aprobadas/marcadas: {len(estado['hechas']) - pendientes_aprobacion}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--informe", action="store_true")
    args = ap.parse_args()
    if args.informe:
        informe()
    else:
        procesar(args.n)


if __name__ == "__main__":
    main()
