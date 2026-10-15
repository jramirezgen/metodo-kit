#!/usr/bin/env python3
"""Backend de consulta del segundo cerebro. Sin LLM, sin embeddings, sin servicio.

Es la interfaz por la que un agente —sobre todo uno LOCAL y pequeño— accede al
conocimiento sin ahogarse. El agente **nunca abre el vault**: llama aquí y recibe
un puñado de fragmentos con su procedencia, dentro de un presupuesto de tokens.

Por qué determinista y no vectorial: 94 notas y 429 KB caben en memoria y se
recorren en milisegundos. Una base vectorial añadiría un servicio, un modelo de
embeddings y una segunda representación del conocimiento que divergiría del
Markdown — el mismo error que ya se pagó con las skills duplicadas. Cuando el
vault pase de ~500 notas se reevalúa; hoy sería sobre-ingeniería medida.

Por qué FRAGMENTOS y no notas enteras: la nota media son ~4 600 caracteres; un
modelo de 9B que reciba tres notas completas ya va cargado y responde peor. Se
devuelve la sección relevante, no el archivo.

Uso:
    python consulta.py "tilt ambiental ley III"                  # texto plano
    python consulta.py "respaldo" --json                          # para un agente
    python consulta.py "fucosa" --tokens 800 --k 3
    python consulta.py --nota "Autoridad Epistémica Local"        # una nota entera
    python consulta.py --mapa                                     # índice + catálogo
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

CHARS_POR_TOKEN = 4
RAIZ_POR_DEFECTO = Path("/mnt/f/OBSIDIAN")

# Pesos: dónde aparece un término importa más que cuántas veces.
PESO_TITULO, PESO_TAGS, PESO_ENCABEZADO, PESO_CUERPO = 12.0, 6.0, 3.0, 1.0

VACIAS = {
    "de", "la", "el", "en", "y", "a", "los", "las", "del", "un", "una", "que",
    "con", "por", "para", "es", "se", "su", "al", "lo", "como", "mas", "o",
    "the", "of", "and", "to", "in", "is", "for", "on",
}


def normalizar(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def terminos(consulta: str) -> list[str]:
    brutos = re.findall(r"[\w²³-]{2,}", normalizar(consulta))
    return [t for t in brutos if t not in VACIAS] or brutos


def secciones(texto: str) -> list[tuple[str, str]]:
    """Parte una nota por encabezados. La unidad recuperable es la sección,
    que es lo que un humano citaría, no un corte cada N caracteres."""
    cuerpo = re.sub(r"\A---\r?\n.*?\r?\n---\r?\n", "", texto, flags=re.DOTALL)
    partes, titulo, buf = [], "", []
    for linea in cuerpo.splitlines():
        if re.match(r"^#{1,4}\s", linea):
            if buf:
                partes.append((titulo, "\n".join(buf).strip()))
            titulo, buf = linea.lstrip("#").strip(), []
        else:
            buf.append(linea)
    if buf:
        partes.append((titulo, "\n".join(buf).strip()))
    return [(t, c) for t, c in partes if c]


def frontmatter(texto: str) -> dict:
    m = re.match(r"\A---\r?\n(.*?)\r?\n---", texto, re.DOTALL)
    if not m:
        return {}
    return {
        k.strip(): v.strip().strip('"')
        for k, v in (l.split(":", 1) for l in m.group(1).splitlines() if ":" in l)
    }


RE_WIKILINK = re.compile(r"\[\[([^\]|#]+)")


def cargar(raiz: Path) -> list[dict]:
    docs = []
    for sub, clase in (("wiki", "nota"), ("alejandria", "documento")):
        base = raiz / sub
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.md")):
            if p.name.startswith("INDICE"):
                continue
            texto = p.read_text(encoding="utf-8", errors="replace")
            fm = frontmatter(texto)
            docs.append({
                "titulo": p.stem, "ruta": str(p.relative_to(raiz)), "clase": clase,
                "tags": fm.get("tags", ""), "resumen": fm.get("resumen", ""),
                "secciones": secciones(texto),
                # Enlaces salientes, ya normalizados: son las aristas del grafo.
                "enlaces": [normalizar(m.strip().split("/")[-1])
                            for m in RE_WIKILINK.findall(texto)],
            })
    return docs


def grafo(docs: list[dict]) -> tuple[dict, dict]:
    """Adyacencia NO dirigida por título normalizado.

    Un enlace `[[A]]` en B significa que A y B se explican mutuamente: para
    recuperar da igual quién apuntó a quién. El vault mide 1 956 enlaces y 10,7
    por nota — esa densidad estaba construida y sin usar: hasta el 2026-08-01
    `consulta.py` era puramente léxico y ninguna herramienta recorría el grafo.
    """
    por_titulo = {normalizar(d["titulo"]): d for d in docs}
    vecinos: dict[str, set[str]] = {t: set() for t in por_titulo}
    for d in docs:
        # ⛔ Solo aristas entre notas de `wiki/`. Los enlaces de `alejandria/` son
        # **procedencia autogenerada** (`## Conexiones de procedencia`, escritas
        # por connect_alexandria_graph.py), no relaciones conceptuales: difundir
        # por ellos no significa nada. Medido el 2026-08-01: las copias de las
        # auditorías del vault (AL-0001/0003/0005/0006) enlazan con casi todo y
        # coincidían léxicamente con casi cualquier consulta sobre el sistema,
        # así que inyectaban el mismo puñado de hubs en 3 de cada 4 búsquedas.
        #
        # El grafo de `wiki/` es lo contrario: curado a mano, una nota un
        # concepto, y cada `[[ ]]` puesto por alguien que decidió ponerlo. Esa es
        # la señal que merece propagarse. Alejandría sigue alcanzándose por
        # léxico, que es como debe alcanzarse un documento íntegro.
        if d["clase"] != "nota":
            continue
        origen = normalizar(d["titulo"])
        for destino in d["enlaces"]:
            if (destino in por_titulo and destino != origen
                    and por_titulo[destino]["clase"] == "nota"):
                vecinos[origen].add(destino)
                vecinos[destino].add(origen)
    return por_titulo, vecinos


def puntuar(doc: dict, terms: list[str]) -> tuple[float, list[tuple[float, str, str]]]:
    n_tit, n_tags = normalizar(doc["titulo"]), normalizar(doc["tags"] + " " + doc["resumen"])
    base = sum(PESO_TITULO for t in terms if t in n_tit)
    base += sum(PESO_TAGS for t in terms if t in n_tags)

    marcadas = []
    for enc, cuerpo in doc["secciones"]:
        n_enc, n_cue = normalizar(enc), normalizar(cuerpo)
        s = sum(PESO_ENCABEZADO for t in terms if t in n_enc)
        # Saturado: una sección que repite el término 20 veces no vale 20 veces
        # más que una que lo dice dos. Evita que un catálogo gane siempre.
        s += sum(PESO_CUERPO * min(n_cue.count(t), 3) for t in terms)
        if s > 0:
            marcadas.append((s, enc, cuerpo))
    marcadas.sort(key=lambda x: -x[0])
    return base + sum(s for s, _, _ in marcadas[:3]), marcadas


# Cuánto de su puntuación cede una nota a sus vecinas.
#
# 🪤 Probado y corregido el 2026-08-01: con difusión plana el grafo EMPEORÓ la
# recuperación. Los hubs (`Grafo de Rescates y Fuentes`, `Mapa de Alejandría`)
# acumulaban un aporte por cada vecino y desplazaban al acierto léxico directo —
# la consulta «por qué el grafo se veía mal» dejó de devolver `Vista de Grafo del
# Vault`, que era exactamente la nota correcta.
#
# Dos correcciones, ambas necesarias:
#  1. El aporte se divide por el GRADO del que lo recibe. Estar enlazado desde
#     todas partes deja de ser mérito: si una nota es vecina de todo, no informa
#     de nada en particular.
#  2. Techo duro: lo difundido nunca supera al mejor acierto léxico. El grafo
#     AÑADE contexto; no secuestra la consulta.
DIFUSION = 0.5
# Techo bajo a propósito: una nota que solo llegó por topología nunca compite con
# una que el texto respalda. Con 0,9 los hubs saturaban el techo y salían en casi
# toda consulta (`Grafo de Rescates y Fuentes`, 3 de 4).
TECHO_DIFUNDIDO = 0.45
# Mínimo de semillas distintas para promover una nota por el grafo. Una sola
# vecina es coincidencia; varias notas pertinentes apuntando al mismo sitio es
# señal. Esto es lo que separa contexto real de ruido de hub.
MIN_SEMILLAS = 2


def buscar(docs: list[dict], consulta: str, k: int, tokens: int,
           difundir: bool = True) -> list[dict]:
    terms = terminos(consulta)
    puntuados = []
    directo: dict[str, float] = {}
    secs_por_titulo: dict[str, list] = {}
    for d in docs:
        s, secs = puntuar(d, terms)
        secs_por_titulo[normalizar(d["titulo"])] = secs
        if s > 0:
            directo[normalizar(d["titulo"])] = s

    # --- Difusión por el grafo (un salto) ---------------------------------
    # Una nota que NO contiene los términos pero está enlazada desde varias que
    # sí, es casi siempre la que explica el porqué. Sin esto la recuperación solo
    # encuentra lo que ya sabías nombrar.
    total = dict(directo)
    via: dict[str, list[str]] = {}
    if difundir and directo:
        por_titulo, vecinos = grafo(docs)
        techo = max(directo.values()) * TECHO_DIFUNDIDO
        for origen, s in directo.items():
            for vecino in vecinos.get(origen, ()):
                # ⛔ A quien YA tiene acierto léxico no se le suma nada: el orden
                # entre aciertos directos lo decide el texto, no la topología.
                # Sumarles difusión reordenaba el ranking y hundía la respuesta
                # correcta (medido: «por qué el grafo se veía mal» pasó del 1º al
                # 3º). El grafo solo puede AÑADIR notas que el léxico no vio.
                if vecino in directo:
                    continue
                # Normalización por AMBOS grados (coseno). Solo por el del
                # receptor no basta: un hub emisor —`Registro de Rescates`, `Kit
                # de Deciframiento`— repartía fuerza plena a sus 40 enlaces y
                # colaba notas sin relación (medido: «cómo se respalda todo»
                # devolvía «Auditoría del caso MO en GEM»). Un enlace desde una
                # nota que enlaza con todo informa menos que uno desde una que
                # enlaza con tres.
                g_o = max(len(vecinos.get(origen, ())), 1)
                g_v = max(len(vecinos.get(vecino, ())), 1)
                aporte = s * DIFUSION / ((g_o * g_v) ** 0.5)
                total[vecino] = min(total.get(vecino, 0.0) + aporte, techo)
                via.setdefault(vecino, []).append(por_titulo[origen]["titulo"])
        por_titulo_all = por_titulo
    else:
        por_titulo_all = {normalizar(d["titulo"]): d for d in docs}

    for t, s in total.items():
        # Una nota traída solo por el grafo necesita varias semillas distintas.
        if t not in directo and len(set(via.get(t, []))) < MIN_SEMILLAS:
            continue
        d = por_titulo_all.get(t)
        if d is not None:
            puntuados.append((s, d, secs_por_titulo.get(t, [])))
    puntuados.sort(key=lambda x: -x[0])

    # Cuota reservada al grafo. Sin ella el grafo nunca paga: los aciertos
    # léxicos llenan el top-k y las notas conectadas —que son las que explican el
    # PORQUÉ— se quedan fuera en cada consulta. Medido el 2026-08-01: `Vista de
    # Grafo del Vault` solo aparecía en «espejos de repositorios» a partir de
    # k=10, y es contexto pertinente.
    if difundir and directo and len(puntuados) > k:
        reserva = max(1, k // 4)
        dir_, graf = [], []
        for fila in puntuados:
            (graf if normalizar(fila[1]["titulo"]) not in directo else dir_).append(fila)
        if graf:
            puntuados = dir_[:k - reserva] + graf[:reserva]
            puntuados.sort(key=lambda x: -x[0])

    # Presupuesto en DOS bolsas. Con una sola, los aciertos léxicos la agotan y
    # las notas del grafo nunca llegan a emitirse aunque tengan plaza en el
    # top-k: reservar asiento sin reservar tokens no sirve de nada (medido).
    presupuesto_total = tokens * CHARS_POR_TOKEN
    hay_grafo = difundir and any(
        normalizar(d["titulo"]) not in directo for _, d, _ in puntuados[:k])
    bolsa_grafo = int(presupuesto_total * 0.25) if hay_grafo else 0

    salida = []
    gastado_dir = gastado_graf = 0
    for s, d, secs in puntuados[:k]:
        nt = normalizar(d["titulo"])
        es_grafo = nt not in directo
        # Una nota que solo llegó por el grafo no tiene sección "relevante" por
        # léxico: se entrega su entrada (la primera sección), que es donde estas
        # notas declaran de qué van.
        if not secs and d["secciones"]:
            secs = [(0.0, d["secciones"][0][0], d["secciones"][0][1])]
        # Las traídas por el grafo son contexto: una sección basta.
        for _, enc, cuerpo in (secs[:1] if es_grafo else secs[:2]) or [(0, "", "")]:
            gastado = gastado_graf if es_grafo else gastado_dir
            presupuesto = bolsa_grafo if es_grafo else presupuesto_total - bolsa_grafo
            if gastado >= presupuesto:
                break
            # Recortar por líneas: cortar a media frase entrega basura al modelo.
            trozo, acum = [], 0
            for linea in cuerpo.splitlines():
                if acum + len(linea) > max(presupuesto - gastado, 300):
                    trozo.append("…")
                    break
                trozo.append(linea)
                acum += len(linea) + 1
            frag = "\n".join(trozo).strip()
            if not frag:
                continue
            if es_grafo:
                gastado_graf += len(frag)
            else:
                gastado_dir += len(frag)
            salida.append({
                "titulo": d["titulo"], "ruta": d["ruta"], "clase": d["clase"],
                "seccion": enc, "texto": frag, "puntuacion": round(s, 1),
                # Procedencia del hallazgo: léxico directo, o traído por el
                # grafo desde qué notas. Un agente debe poder distinguirlo.
                "via": "léxico" if nt in directo else "grafo",
                "enlazado_desde": sorted(set(via.get(nt, [])))[:3],
            })
    return salida


def mapa(raiz: Path) -> dict:
    """Lo mínimo para orientarse: los dos catálogos, sin abrir ninguna nota."""
    idx = (raiz / "index.md")
    cat = (raiz / "alejandria" / "INDICE.md")
    return {
        "index_tokens": len(idx.read_text(encoding="utf-8")) // CHARS_POR_TOKEN if idx.is_file() else 0,
        "catalogo_tokens": len(cat.read_text(encoding="utf-8")) // CHARS_POR_TOKEN if cat.is_file() else 0,
        "index": str(idx), "catalogo": str(cat),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("consulta", nargs="?", default="")
    ap.add_argument("--raiz", type=Path, default=RAIZ_POR_DEFECTO)
    ap.add_argument("--k", type=int, default=5, help="documentos distintos como máximo")
    ap.add_argument("--tokens", type=int, default=1200, help="presupuesto de salida")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--nota", help="devuelve una nota concreta por su título")
    ap.add_argument("--mapa", action="store_true")
    ap.add_argument("--sin-grafo", action="store_true",
                    help="solo emparejamiento léxico, sin difundir por enlaces")
    args = ap.parse_args()

    if args.mapa:
        print(json.dumps(mapa(args.raiz), ensure_ascii=False, indent=2))
        return

    if args.nota:
        for d in cargar(args.raiz):
            if normalizar(d["titulo"]) == normalizar(args.nota):
                p = args.raiz / d["ruta"]
                print(p.read_text(encoding="utf-8"))
                return
        sys.exit(f"No existe la nota «{args.nota}».")

    if not args.consulta:
        sys.exit("Falta la consulta. Usa --mapa o --nota si buscas otra cosa.")

    res = buscar(cargar(args.raiz), args.consulta, args.k, args.tokens,
                 difundir=not args.sin_grafo)
    if args.json:
        print(json.dumps({"consulta": args.consulta, "resultados": res},
                         ensure_ascii=False, indent=2))
        return

    if not res:
        print(f"Sin resultados para «{args.consulta}».")
        return
    coste = sum(len(r["texto"]) for r in res) // CHARS_POR_TOKEN
    n_grafo = sum(1 for r in res if r["via"] == "grafo")
    extra = f", {n_grafo} traídos por el grafo" if n_grafo else ""
    print(f"# {len(res)} fragmentos (~{coste} tokens{extra}) — «{args.consulta}»\n")
    for r in res:
        cab = f"{r['titulo']}" + (f" › {r['seccion']}" if r["seccion"] else "")
        print(f"## {cab}\n_{r['ruta']}_")
        if r["via"] == "grafo":
            print(f"⇢ _traída por el grafo desde: {', '.join(r['enlazado_desde'])}_")
        print(f"\n{r['texto']}\n")


if __name__ == "__main__":
    main()
