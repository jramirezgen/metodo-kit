# -*- coding: utf-8 -*-
"""plan_canvas_lib — un canvas legible a partir de `plan/plan.json` + `registro/nodos.jsonl`.

Por qué existe
--------------
El DAG de un proyecto (skill `dag-de-proyecto`) es la fuente del plan, y el estado de
cada nodo sale del registro. Dibujar ese DAG a mano es el defecto que esta skill ya
documenta: un mapa mantenido a mano se desincroniza. Esta librería lo **genera**, con la
misma compuerta de legibilidad que cualquier otro canvas (`canvas_lib.informe`).

Una *vista* es un recorte del DAG por `fase`. Los nodos de otras fases de los que depende
la vista aparecen a la izquierda como referencias ("viene de") y los que dependen de ella,
a la derecha ("alimenta a"), para que la vista se pueda recorrer sin abrir las demás.

Reglas de dibujo (cada una evita un defecto de lectura):
  · la columna de un nodo es su profundidad **dentro de la vista**; ninguna arista va hacia
    atrás ni cae en su propia columna;
  · se dibuja la **reducción transitiva**: si A→B→C, no se pinta además A→C;
  · el color lo da el ESTADO (registro), nunca un valor escrito en el generador;
  · una arista sin etiqueta no puede quedar tapada: ésta no añade etiquetas.

Sin dependencias: solo stdlib y `canvas_lib`. Se vendoriza a `docs/wiki/` de cada repo.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from canvas_lib import Lienzo, informe

VERSION = "1.0.0"

CERRADO = {"hecho", "juzgado"}

ICONOS = {
    "doc": "📄", "decision": "⚖️", "insumo": "📥", "infra": "🔧", "dominio": "🧩",
    "adaptador": "🔌", "preinscripcion": "📝", "corrida": "🏃", "medicion": "📏",
    "eureka": "⭐", "revision": "🔍", "release": "🚀", "externo": "🔗", "dato": "🗃️",
}

#: Caracteres por línea que caben en un nodo de ancho estándar, y alto por línea.
_CPL = 70
_PX_LINEA = 34


def cargar(raiz) -> tuple:
    """`(plan, nodos)` con el estado del registro aplicado (manda la última línea)."""
    raiz = Path(raiz)
    plan = json.loads((raiz / "plan" / "plan.json").read_text(encoding="utf-8"))
    ultimo = {}
    reg = raiz / "registro" / "nodos.jsonl"
    if reg.is_file():
        for linea in reg.read_text(encoding="utf-8").splitlines():
            if linea.strip():
                y = json.loads(linea)
                ultimo[y["nodo"]] = y
    nodos = []
    for x in plan["nodos"]:
        y = dict(x)
        if x["id"] in ultimo:
            y["estado"] = ultimo[x["id"]]["estado"]
            y["evidencia"] = ultimo[x["id"]].get("evidencia")
        nodos.append(y)
    return plan, nodos


def _alto(texto: str) -> int:
    lineas = sum(max(1, math.ceil(len(l) / _CPL)) for l in texto.split("\n"))
    return max(170, _PX_LINEA * lineas + 56)


def _color(x: dict, listo: bool):
    e = x["estado"]
    if e in CERRADO:
        return "4"
    if e == "en_curso":
        return "2"
    if e in ("bloqueado", "pausado"):
        return "1"
    return "3" if listo else None


def _texto(x: dict, por_id: dict) -> str:
    cerrado = x["estado"] in CERRADO
    abiertas = [d for d in x["depende_de"] if por_id[d]["estado"] not in CERRADO]
    if cerrado:
        sit = ""
    elif not abiertas:
        sit = " · listo para empezar"
    else:
        sit = " · espera " + ", ".join(abiertas[:3]) + ("…" if len(abiertas) > 3 else "")
    icono = ICONOS.get(x["tipo"], "▫️")
    lineas = [f"## {icono} {x['id']} · {x['titulo']}",
              f"`{x['tipo']}` · **{x['estado']}**{sit}",
              f"**Entrega:** {x['entrega']}"]
    if cerrado:
        lineas.append(f"**Evidencia:** `{x.get('evidencia')}`")
    else:
        lineas.append(f"**Hecho cuando:** {x['hecho_cuando']}")
    return "\n".join(lineas)


def _reducir(deps: dict) -> dict:
    """Reducción transitiva de `{id: {dependencias dentro de la vista}}`."""
    memo = {}

    def alcanza(n):
        if n not in memo:
            r = set()
            for d in deps.get(n, ()):
                r |= {d} | alcanza(d)
            memo[n] = r
        return memo[n]

    return {n: {d for d in ds if not any(d in alcanza(m) for m in ds if m != d)}
            for n, ds in deps.items()}


def construir(raiz, *, fases, titulo: str, subtitulo: str = "") -> Lienzo:
    """Dibuja la vista del DAG formada por los nodos de las `fases` dadas."""
    plan, nodos = cargar(raiz)
    por_id = {x["id"]: x for x in nodos}
    orden = {f: i for i, f in enumerate(fases)}
    vista = [x for x in nodos if x.get("fase") in orden]
    if not vista:
        raise ValueError(f"ningún nodo en las fases {list(fases)}")
    ids = {x["id"] for x in vista}

    deps = {x["id"]: {d for d in x["depende_de"] if d in ids} for x in vista}
    nivel = {}

    def prof(i):
        if i not in nivel:
            nivel[i] = 0 if not deps[i] else 1 + max(prof(d) for d in deps[i])
        return nivel[i]

    for i in ids:
        prof(i)
    reducido = _reducir(deps)

    viene = sorted({d for x in vista for d in x["depende_de"] if d not in ids},
                   key=lambda i: list(por_id).index(i))
    va_a = sorted({y["id"] for y in nodos if y["id"] not in ids
                   and any(d in ids for d in y["depende_de"])},
                  key=lambda i: list(por_id).index(i))
    maxn = max(nivel.values())
    cols = ["leyenda"] + (["viene"] if viene else []) + [f"n{k}" for k in range(maxn + 1)] \
        + (["va"] if va_a else [])
    L = Lienzo()
    C = L.columnas(*cols, desde=-1400)

    cerrados = sum(1 for x in vista if x["estado"] in CERRADO)
    leyenda = (f"## {titulo}\n*{subtitulo}*\n\n" if subtitulo else f"## {titulo}\n\n")
    leyenda += (f"**{cerrados} de {len(vista)}** nodos cerrados · plan v{plan.get('version_plan')} "
                f"· {plan.get('fecha')}\n\n"
                "🟩 hecho (con su commit) · 🟨 listo para empezar · 🟧 en curso\n"
                "🟥 bloqueado o pausado · ⬜ espera a otro nodo\n\n"
                "Generado desde `plan/plan.json` y `registro/`: no se edita a mano.")
    L.nodo("leyenda", C["leyenda"], 0, L.ancho, _alto(leyenda) + 60, leyenda, "6")

    def listo(x):
        return all(por_id[d]["estado"] in CERRADO for d in x["depende_de"])

    if viene:
        p = L.pila("viene", 0)
        for i in viene:
            y = por_id[i]
            t = f"↩ **{i}** · {y['titulo']}\n*otra vista · {y['estado']}*"
            p.add(f"r_{i}", _alto(t), t)
        p.cerrar("g_viene", "VIENE DE OTRAS VISTAS")
    for k in range(maxn + 1):
        p = L.pila(f"n{k}", 0)
        for x in sorted((y for y in vista if nivel[y["id"]] == k),
                        key=lambda y: (orden[y["fase"]], list(por_id).index(y["id"]))):
            t = _texto(x, por_id)
            p.add(x["id"], _alto(t), t, _color(x, listo(x)))
        p.cerrar(f"g_n{k}", f"PASO {k + 1}")
    if va_a:
        p = L.pila("va", 0)
        for i in va_a:
            y = por_id[i]
            t = f"↪ **{i}** · {y['titulo']}\n*otra vista · {y['estado']}*"
            p.add(f"s_{i}", _alto(t), t)
        p.cerrar("g_va", "ALIMENTA A")

    for x in vista:
        for d in sorted(reducido[x["id"]]):
            L.arista(d, x["id"])
        for d in x["depende_de"]:
            if d not in ids:
                L.arista(f"r_{d}", x["id"])
    for i in va_a:
        for d in por_id[i]["depende_de"]:
            if d in ids:
                L.arista(d, f"s_{i}")
    return L


def escribir(raiz, salida, *, fases, titulo: str, subtitulo: str = "") -> None:
    """Construye, pasa la compuerta de legibilidad y escribe. Se niega si no pasa."""
    L = construir(raiz, fases=fases, titulo=titulo, subtitulo=subtitulo)
    ok, lineas = informe(L.a_dict(), libres={"leyenda"})
    for l in lineas:
        print("  " + l)
    if not ok:
        raise SystemExit("✗ no se escribe un canvas con etiquetas ilegibles")
    L.escribir(salida)
    print(f"→ {salida}")
