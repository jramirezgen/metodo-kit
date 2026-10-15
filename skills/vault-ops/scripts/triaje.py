#!/usr/bin/env python3
"""Triaje de `raw/bandeja/` con el modelo LOCAL (Amadeus). Propone, no destruye.

El cuello de botella del segundo cerebro nunca fue extraer texto: los 888 `.md` de
la bandeja ya son Markdown. Era **decidir** qué merece nota, qué merece
conservarse íntegro y qué es ruido. Esa decisión es barata para un modelo pequeño
y cara para un humano, así que es exactamente lo que debe automatizarse.

## Reparto de trabajo (lo que un 9B puede y lo que no)

| Tarea | Quién | Por qué |
| --- | --- | --- |
| Extraer rasgos (tamaño, encabezados, inicio) | script | determinista, sin modelo |
| **Clasificar** en 4 destinos | modelo local | acierta y cuesta ~0,35 s |
| Redactar el `resumen` de Alejandría | modelo local | cabe en su capacidad |
| **Sintetizar** una nota de `wiki/` | ⛔ NADIE aquí | exige leer el documento entero y decidir qué es cierto; se marca como candidata |
| Mover archivos | script, con `--aplicar` | el modelo nunca toca el disco |

## Configuración del modelo, medida y no supuesta

`think:false` es **obligatorio**. Qwen3.5 es un razonador: sin desactivar el
pensamiento consumió 900 tokens y 22 s para devolver una respuesta **vacía**. Con
`think:false` + `format:json` + `temperature:0` responde JSON válido en **0,35 s**.

Uso:
    python triaje.py                      # propone sobre 25 archivos (prueba)
    python triaje.py --n 0                # todos los pendientes
    python triaje.py --aplicar            # ejecuta lo ya propuesto
    python triaje.py --informe            # resumen de lo decidido
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path("/mnt/f/OBSIDIAN")
BANDEJA = RAIZ / "raw" / "bandeja"
DESCARTE = RAIZ / "raw" / "descarte"
ESTADO = RAIZ / "raw" / "_triaje_estado.json"
OLLAMA = "http://127.0.0.1:11434/api/generate"
MODELO = "qwen3.5:9b"

DESTINOS = {
    "ALEJANDRIA": "documento largo que vale por su texto íntegro",
    "CANDIDATA_WIKI": "concepto que merece una nota sintética (la escribe un humano o un modelo mayor)",
    "CAPACIDAD": "procedimiento reutilizable, candidato a skill",
    "RUIDO": "sin valor recuperable: vacío, sin título, restos de exportación",
}

SISTEMA = (
    "Clasificas documentos de una bandeja de entrada para un sistema de gestión "
    "del conocimiento. Respondes SIEMPRE JSON válido y nada más."
)


def rasgos(p: Path) -> dict:
    """Todo lo que se puede saber sin modelo. Cuanto más aporte esto, menos
    tiene que adivinar el modelo y más estable es la clasificación."""
    texto = p.read_text(encoding="utf-8", errors="replace")
    cuerpo = re.sub(r"\A﻿?---\r?\n.*?\r?\n---\r?\n", "", texto, flags=re.DOTALL)
    encabezados = [h.strip() for h in re.findall(r"^#{1,3}\s+(.+)$", cuerpo, re.M)][:8]
    inicio = "\n".join(l for l in cuerpo.splitlines() if l.strip())[:600]
    return {
        "ruta": str(p.relative_to(RAIZ)),
        "nombre": p.stem,
        "kb": round(p.stat().st_size / 1024, 1),
        "carpeta": str(p.parent.relative_to(BANDEJA)),
        "n_encabezados": len(encabezados),
        "encabezados": encabezados,
        "inicio": inicio,
        "chars_utiles": len(cuerpo.strip()),
    }


def regla_dura(r: dict) -> str | None:
    """Lo que no hace falta preguntarle a ningún modelo. Un archivo casi vacío o
    sin título es ruido por definición; gastar 0,35 s en confirmarlo es tirar
    tiempo, y además el modelo a veces se inventa valor donde no lo hay."""
    if r["chars_utiles"] < 200:
        return "RUIDO"
    if r["nombre"].startswith("sin-titulo") and r["chars_utiles"] < 1500:
        return "RUIDO"
    return None


# Umbral medido: por debajo de ~4 KB un documento no "vale por su texto íntegro".
# Es un resumen, un abstract o una portada; su sitio es una nota o el descarte.
KB_MINIMO_ALEJANDRIA = 4.0


def postcondicion(dec: dict, r: dict) -> dict:
    """El modelo PROPONE, las reglas DISPONEN.

    Dos fallos de calibración medidos sobre 25 clasificaciones reales:

    1. La confianza se satura en 0.98 para todo — no discrimina, así que no se
       puede usar como compuerta. Se conserva por trazabilidad y nada más.
    2. El modelo colapsa casi todo en ALEJANDRIA, incluidos abstracts de 1 KB.

    Contra el segundo hay defensa determinista: el tamaño es un hecho, no una
    opinión. Un documento pequeño clasificado como «vale por su texto íntegro»
    se degrada a candidato a nota, que es lo que realmente es.
    """
    if dec["destino"] == "ALEJANDRIA" and r["kb"] < KB_MINIMO_ALEJANDRIA:
        dec["destino"] = "CANDIDATA_WIKI"
        dec["ajuste"] = (f"degradado de ALEJANDRIA: {r['kb']} KB < "
                         f"{KB_MINIMO_ALEJANDRIA} KB, no vale por su texto íntegro")
    return dec


def preguntar(r: dict, reintentos: int = 2) -> dict | None:
    prompt = (
        f"{SISTEMA}\n\nDestinos posibles:\n"
        + "\n".join(f"- {k}: {v}" for k, v in DESTINOS.items())
        + f"\n\nDocumento:\n- nombre: {r['nombre']}\n- carpeta: {r['carpeta']}\n"
        f"- tamaño: {r['kb']} KB\n- encabezados: {' | '.join(r['encabezados']) or '(ninguno)'}\n"
        f"- inicio:\n{r['inicio']}\n\n"
        "Responde JSON con claves exactas: destino (uno de los cuatro), "
        "confianza (0.0-1.0), resumen (una frase de máximo 25 palabras que diga "
        "CUÁNDO haría falta este documento, no de qué trata)."
    )
    cuerpo = json.dumps({
        "model": MODELO, "prompt": prompt, "stream": False,
        "think": False, "format": "json",
        "options": {"temperature": 0, "num_predict": 250},
    }).encode()

    for intento in range(reintentos):
        try:
            req = urllib.request.Request(OLLAMA, data=cuerpo,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                d = json.loads(resp.read())
            out = json.loads(d.get("response", "") or "{}")
            destino = str(out.get("destino", "")).upper().strip()
            if destino in DESTINOS:
                return {
                    "destino": destino,
                    "confianza": float(out.get("confianza", 0) or 0),
                    "resumen": str(out.get("resumen", ""))[:220].strip(),
                }
        except (urllib.error.URLError, json.JSONDecodeError, ValueError, TypeError):
            pass
        time.sleep(0.5 * (intento + 1))
    return None  # el modelo falló: se deja pendiente, NO se adivina


def cargar_estado() -> dict:
    if ESTADO.is_file():
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    return {"decisiones": {}, "fallos": []}


def guardar_estado(e: dict) -> None:
    ESTADO.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")


def pendientes(estado: dict) -> list[Path]:
    return [p for p in sorted(BANDEJA.rglob("*.md"))
            if str(p.relative_to(RAIZ)) not in estado["decisiones"]]


def clasificar(n: int) -> None:
    estado = cargar_estado()
    cola = pendientes(estado)
    if n > 0:
        cola = cola[:n]
    if not cola:
        print("No quedan archivos pendientes.")
        return

    print(f"Clasificando {len(cola)} archivos con {MODELO} (local)…")
    t0, por_regla, por_modelo, fallidos = time.time(), 0, 0, 0
    for i, p in enumerate(cola, 1):
        r = rasgos(p)
        dura = regla_dura(r)
        if dura:
            dec = {"destino": dura, "confianza": 1.0,
                   "resumen": "descartado por regla determinista (sin contenido útil)",
                   "via": "regla"}
            por_regla += 1
        else:
            out = preguntar(r)
            if out is None:
                estado["fallos"].append(r["ruta"])
                fallidos += 1
                continue
            dec = postcondicion({**out, "via": "modelo"}, r)
            por_modelo += 1
        dec.update(kb=r["kb"], carpeta=r["carpeta"], nombre=r["nombre"])
        estado["decisiones"][r["ruta"]] = dec
        if i % 25 == 0 or i == len(cola):
            guardar_estado(estado)
            print(f"  {i}/{len(cola)}  ({time.time()-t0:.0f}s)")
    guardar_estado(estado)
    print(f"\nregla dura: {por_regla} | modelo: {por_modelo} | fallidos: {fallidos}")
    print(f"tiempo: {time.time()-t0:.0f}s — estado en {ESTADO.relative_to(RAIZ)}")


def informe() -> None:
    estado = cargar_estado()
    d = estado["decisiones"]
    if not d:
        print("Nada clasificado todavía.")
        return
    from collections import Counter
    c = Counter(v["destino"] for v in d.values())
    total = sum(c.values())
    print(f"# Triaje — {total} archivos clasificados, {len(pendientes(estado))} pendientes\n")
    print("| Destino | Archivos | % |\n| --- | --- | --- |")
    for k, n in c.most_common():
        print(f"| {k} | {n} | {100*n/total:.0f}% |")
    ajustadas = [r for r, v in d.items() if v.get("ajuste")]
    confs = {round(v["confianza"], 2) for v in d.values() if v["via"] == "modelo"}
    print(f"\nCorregidas por postcondición determinista: **{len(ajustadas)}**")
    print(f"Valores distintos de confianza que emite el modelo: {sorted(confs)}")
    if len(confs) <= 3:
        print("  ⚠️ la confianza está SATURADA: no discrimina, no sirve como compuerta.")
    if estado["fallos"]:
        print(f"\n⚠️ {len(estado['fallos'])} archivos que el modelo no supo clasificar (siguen pendientes).")


def aplicar(minimo: float) -> None:
    """Mueve SOLO lo inequívoco. Nada se borra: RUIDO va a raw/descarte/."""
    estado = cargar_estado()
    DESCARTE.mkdir(parents=True, exist_ok=True)
    movidos, saltados = 0, 0
    for ruta, dec in sorted(estado["decisiones"].items()):
        src = RAIZ / ruta
        if not src.is_file():
            continue
        # No se filtra por confianza: está saturada y no significa nada. La
        # compuerta real es que RUIDO solo se mueve a descarte/, nunca se borra.
        if dec["destino"] != "RUIDO":
            saltados += 1
            continue
        dst = DESCARTE / src.relative_to(BANDEJA)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        movidos += 1
    print(f"Movidos a raw/descarte/: {movidos}. Sin tocar: {saltados}.")
    print("ALEJANDRIA y CANDIDATA_WIKI NO se mueven automáticamente:")
    print("  - Alejandría exige un ID que nunca se reasigna y un resumen decisorio.")
    print("  - wiki/ exige síntesis verificada, fuera del alcance de un 9B.")
    print("Usa --informe para ver la cola y derivarlos con criterio.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=25, help="cuántos clasificar (0 = todos)")
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--informe", action="store_true")
    ap.add_argument("--min-confianza", type=float, default=0.8)
    args = ap.parse_args()

    if not BANDEJA.is_dir():
        sys.exit(f"No existe {BANDEJA}")
    if args.informe:
        informe()
    elif args.aplicar:
        aplicar(args.min_confianza)
    else:
        clasificar(args.n)


if __name__ == "__main__":
    main()
