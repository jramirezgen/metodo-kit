#!/usr/bin/env python3
"""Mide el estado de un vault Obsidian usado como memoria de agentes LLM.

Fuente ÚNICA de las cifras del vault. Toda auditoría en prosa debe citar este
script, nunca recontar a mano: los conteos manuales se desincronizan en cuanto
alguien añade una nota, y una auditoría con cifras rancias es peor que ninguna.

Mide FORMA, ESTRUCTURA y ECONOMÍA. No verifica que el contenido sea cierto —
eso es trabajo humano y el reporte lo dice explícitamente.

Uso:
    python vault_audit.py <raiz_vault> [--json salida.json] [--md salida.md]
    python vault_audit.py <raiz_vault> --censo-raw censo.csv

Contrato:
  - <raiz_vault> debe existir y contener wiki/ e index.md, o aborta.
  - NUNCA lee dentro de _PRIVADO/ (credenciales sin cifrar). Ni siquiera lista
    sus archivos: solo confirma que existe y lo salta.
  - No escribe nada dentro del vault salvo que se le pase --json/--md/--censo-raw
    con una ruta explícita.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# Directorios que nunca se recorren. _PRIVADO por seguridad; el resto por ruido.
EXCLUIR_SIEMPRE = {"_PRIVADO", ".obsidian", ".git", ".stfolder", "node_modules", ".venv"}
EXCLUIR_PREFIJOS = ("_archivo_", "archive", "snapshot_")

CAMPOS_FRONTMATTER = ("tags", "creado", "actualizado", "fuente")

# Eje Área/Tema (2026-07-30). Vocabulario CERRADO: una nota que declare un área
# fuera de esta lista desaparece de las consultas Dataview sin avisar de nada,
# que es el modo de fallo más caro de un esquema por propiedades.
AREAS_VALIDAS = frozenset({
    "Investigación", "Empresa", "Sistema", "Conocimiento",
    "Relaciones", "Clientes", "Finanzas", "Salud", "Talleres",
})
RE_AREA = re.compile(r"^area:\s*\[(.*?)\]\s*$", re.M)
RE_TEMA = re.compile(r"^tema:\s*\[(.*?)\]\s*$", re.M)

# Un token ≈ 4 caracteres. Es una aproximación, no una medición — el reporte la
# etiqueta como tal. Sirve para comparar magnitudes (¿factor 3 o factor 30?),
# no para presupuestar al token.
CHARS_POR_TOKEN = 4

RE_WIKILINK = re.compile(r"\[\[([^\]\n|#]+)")
RE_FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---", re.DOTALL)


def _excluido(rel: Path) -> bool:
    for parte in rel.parts:
        if parte in EXCLUIR_SIEMPRE or parte.startswith(EXCLUIR_PREFIJOS):
            return True
    return False


def notas_de(raiz: Path, subdir: str) -> list[Path]:
    base = raiz / subdir
    if not base.is_dir():
        return []
    return sorted(
        p for p in base.rglob("*.md") if not _excluido(p.relative_to(raiz))
    )


def adjuntos_de(raiz: Path, *subdirs: str) -> set[str]:
    """Los nombres de fichero que Obsidian resuelve y que NO son notas.

    ⛔ **El defecto que esto cierra, medido el 2026-09-08.** `resolubles` se
    construía sólo con los `.md`, así que un `[[Mapa.canvas]]` con el fichero
    delante se reportaba **roto**. Publicar los dos canvas de ELEMENT en
    `wiki/ELEMENT/` dejó la compuerta en 2 enlaces rotos —y `certificar.sh`
    falla con uno—, o sea que **publicar un mapa rompía la compuerta**.

    Obsidian resuelve un adjunto por su nombre de fichero **con** extensión
    (`[[Mapa.canvas]]`), a diferencia de una nota, que se cita sin ella. Por eso
    esto devuelve nombres completos y no `stem`: mezclarlos en el mismo conjunto
    no colisiona.

    Sólo se recorren los subdirectorios **curados** que se le pasen: `raw/`
    (204 MB) nunca entra, ni siquiera para esto.
    """
    nombres: set[str] = set()
    for subdir in subdirs:
        base = raiz / subdir
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() != ".md" \
                    and not _excluido(p.relative_to(raiz)):
                nombres.add(p.name)
    return nombres


def leer(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def campos_frontmatter(texto: str) -> set[str]:
    m = RE_FRONTMATTER.match(texto)
    if not m:
        return set()
    return {
        linea.split(":", 1)[0].strip()
        for linea in m.group(1).splitlines()
        if ":" in linea and not linea.startswith((" ", "\t", "-"))
    }


def enlaces_de(texto: str) -> list[str]:
    """Wikilinks reales. Descarta `[[ ]]` citado como ejemplo y los partidos
    por salto de línea, que Obsidian NO resuelve — son enlaces rotos de hecho.

    Dentro de una tabla el alias se escribe `[[Nota\\|alias]]`: la barra escapa
    el `|` para que no parta la celda, y Obsidian resuelve `Nota`. Sin quitarla,
    los 9 enlaces así escritos contaban como rotos (medido 2026-09-28)."""
    salida = []
    for bruto in RE_WIKILINK.findall(texto):
        destino = bruto.strip().removesuffix("\\").rstrip()
        if destino and "\n" not in bruto:
            salida.append(destino)
    return salida


def _indice_con_sus_submapas(raiz: Path, indice: Path) -> tuple[str, set[str]]:
    """El texto del mapa completo: `index.md` **más** los sub-mapas que enlaza.

    ⛔ **El defecto que esto cierra, medido el 2026-09-07.** `index.md` pesaba
    **25 142 tokens** contra un techo de 10 000, y el 72 % —18 053— era una sola
    sección con 242 notas. Partirla es exactamente lo que la compuerta pide; pero
    con `indexadas` mirando sólo `index.md`, partir el mapa habría reportado
    **242 notas no indexadas** de golpe. O sea: la compuerta castigaba el arreglo
    que ella misma exige.

    Un sub-mapa es un `.md` de la RAÍZ enlazado desde `index.md`. Se pide por
    enlace y no por nombre a propósito: un fichero suelto que se llame
    `index_loquesea.md` y que nadie enlace **tiene** que seguir apareciendo como
    basura en la raíz. El mapa es el que se recorre, no el que se llama mapa.

    El recorrido es **transitivo**: un sub-mapa de un sub-mapa sigue siendo
    mapa. `index.md` ya no enlaza las notas de ELEMENT —las enlaza
    `index_TGDE.md`—, así que exigir que las colecciones de un proyecto colgaran
    del índice maestro sería devolverle justo el detalle que la partición del
    2026-09-07 le quitó. Cada salto sigue pidiendo su prueba (fichero de la raíz
    enlazado, o `submapa: true` declarado), así que la transitividad no vacía la
    compuerta: la hace seguir la forma real del mapa.

    Sin sub-mapas devuelve exactamente el texto de siempre y un conjunto vacío:
    un vault que no ha partido nada no nota que esto existe.
    """
    submapas: set[str] = set()
    por_nombre = {p.stem: p for p in (raiz / "wiki").rglob("*.md")
                  if not _excluido(p.relative_to(raiz))}
    vistos = {indice.resolve()}
    textos = [leer(indice)]
    pendientes = [textos[0]]
    while pendientes:
        for destino in re.findall(r"\[\[([^\]\|#\n]+)", pendientes.pop()):
            d = destino.strip()
            candidato = raiz / f"{d}.md"
            if candidato.is_file() and candidato.parent == raiz:
                ruta = candidato
            else:
                # Un índice de COLECCIÓN (`wiki/<PROY>/<algo>/00 — ...md`)
                # también es media mitad del mapa, y meter sus hijas una a una
                # en el índice es exactamente lo que infló `index_TGDE.md` a 181
                # ganchos de ~87 tokens. Se reconoce por DOS cosas a la vez,
                # nunca por el nombre ni por la carpeta: lo enlaza el mapa **y**
                # se declara `submapa: true`. Sin la declaración, cualquiera de
                # los ~174 conceptos que `index.md` enlaza arrastraría a sus
                # vecinos y la compuerta se quedaría hueca.
                hijo = por_nombre.get(d)
                ruta = hijo if hijo is not None and _declara_submapa(leer(hijo)) else None
            if ruta is None or ruta.resolve() in vistos:
                continue
            vistos.add(ruta.resolve())
            submapas.add(ruta.name)
            textos.append(leer(ruta))
            pendientes.append(textos[-1])
    return "\n".join(textos), submapas


def _declara_submapa(texto: str) -> bool:
    m = RE_FRONTMATTER.search(texto)
    return bool(m) and re.search(r"^submapa:\s*true\s*$", m.group(1), re.M) is not None


def medir(raiz: Path) -> dict:
    if not raiz.is_dir():
        sys.exit(f"ERROR: no existe la raíz del vault: {raiz}")
    if not (raiz / "wiki").is_dir():
        sys.exit(f"ERROR: {raiz} no tiene wiki/ — ¿es realmente un vault?")
    indice = raiz / "index.md"
    if not indice.is_file():
        sys.exit(f"ERROR: {raiz} no tiene index.md — el mapa es obligatorio.")

    notas = notas_de(raiz, "wiki")
    texto_indice, submapas = _indice_con_sus_submapas(raiz, indice)

    por_nombre: dict[str, Path] = {}
    contenidos: dict[Path, str] = {}
    duplicados: list[str] = []
    for p in notas:
        contenidos[p] = leer(p)
        if p.stem in por_nombre:
            duplicados.append(p.stem)
        por_nombre[p.stem] = p

    # Notas fuera de wiki/ pero en la raíz: rompen la estructura declarada.
    # Excepción: los archivos de PROTOCOLO. No son notas de conocimiento, son las
    # puertas de entrada de cada agente, y su convención les exige vivir en la
    # raíz: `CLAUDE.md` (Claude Code) y `AGENTS.md` (Codex; symlinkeado desde
    # ~/.codex/ y desde el workspace). Añadido 2026-08-01, cuando la compuerta
    # cazó AGENTS.md correctamente y la respuesta correcta fue declarar la
    # excepción, no mover el archivo a un sitio donde Codex no lo lee.
    PROTOCOLO_EN_RAIZ = ("index.md", "CLAUDE.md", "AGENTS.md")
    # Un sub-mapa que `index.md` enlaza tampoco es una nota suelta: es la otra
    # mitad del mapa. Se reconoce por estar ENLAZADO desde el índice, no por
    # llamarse `index_*` — un fichero con el nombre de un mapa que nadie enlaza
    # sí es basura en la raíz, y tiene que seguir saliendo aquí.
    sueltas = [
        p.name for p in raiz.glob("*.md")
        if p.name not in PROTOCOLO_EN_RAIZ and not p.name.startswith("_")
        and p.name not in submapas
    ]

    chars = sum(len(t) for t in contenidos.values())

    frontmatter_incompleto, vacias = [], []
    sin_area, area_invalida, sin_tema = [], [], []
    temas_por_nota: list[dict] = []
    temas_en_uso: Counter = Counter()
    reparto_areas: Counter = Counter()
    marcadas, sin_verificar = 0, 0
    salientes: dict[str, list[str]] = {}
    entrantes: Counter = Counter()
    rotos: dict[str, list[str]] = {}

    resolubles = (set(por_nombre) | {p.stem for p in raiz.glob("*.md")}
                  | adjuntos_de(raiz, "wiki", "alejandria"))

    for p, texto in contenidos.items():
        nombre = p.stem
        if not texto.strip():
            vacias.append(nombre)
        if not set(CAMPOS_FRONTMATTER) <= campos_frontmatter(texto):
            faltan = sorted(set(CAMPOS_FRONTMATTER) - campos_frontmatter(texto))
            frontmatter_incompleto.append({"nota": nombre, "faltan": faltan})
        # Eje Área/Tema. Se comprueba solo en wiki/: alejandria/ no lo usa.
        if p.is_relative_to(raiz / "wiki"):
            m_area = RE_AREA.search(texto)
            if not m_area:
                sin_area.append(nombre)
            else:
                declaradas = [x.strip().strip("\"'") for x in m_area.group(1).split(",") if x.strip()]
                malas = [x for x in declaradas if x not in AREAS_VALIDAS]
                if malas:
                    area_invalida.append({"nota": nombre, "areas": malas})
                for x in declaradas:
                    reparto_areas[x] += 1
            m_tema = RE_TEMA.search(texto)
            if not m_tema or not m_tema.group(1).strip():
                sin_tema.append(nombre)
            else:
                propios = []
                for t in m_tema.group(1).split(","):
                    if t.strip():
                        limpio = t.strip().strip("\"'")
                        temas_en_uso[limpio] += 1
                        propios.append(limpio)
                temas_por_nota.append({"nota": nombre, "temas": propios})

        if "⚠️" in texto:
            marcadas += 1
        sin_verificar += texto.lower().count("sin verificar")

        enlaces = enlaces_de(texto)
        salientes[nombre] = enlaces
        for destino in enlaces:
            # Enlaces por RUTA (transclusiones tipo ![[alejandria/X/Y.md]]): se
            # validan contra el disco, no contra los nombres de nota.
            if "/" in destino:
                if not (raiz / destino).is_file():
                    rotos.setdefault(destino, []).append(nombre)
                continue
            if destino in resolubles:
                entrantes[destino] += 1
            else:
                rotos.setdefault(destino, []).append(nombre)

    # Transclusiones por ruta completa: se validan contra el disco.
    transclusiones_rotas = []
    for p, texto in contenidos.items():
        for ruta in re.findall(r"!\[\[([^\]\n]+\.md)\]\]", texto):
            if not (raiz / ruta).is_file():
                transclusiones_rotas.append({"nota": p.stem, "ruta": ruta})

    indexadas = {n for n in por_nombre if f"[[{n}" in texto_indice}
    huerfanas_salida = sorted(n for n, e in salientes.items() if not e)
    huerfanas_entrada = sorted(n for n in por_nombre if entrantes[n] == 0)
    total_enlaces = sum(len(e) for e in salientes.values())

    # Higiene: sub-bóvedas anidadas dentro de wiki/ (la trampa ya pagada).
    subbovedas = [
        str(d.relative_to(raiz)) for d in (raiz / "wiki").rglob(".obsidian") if d.is_dir()
    ]

    tokens_wiki = chars // CHARS_POR_TOKEN
    tokens_indice = len(texto_indice) // CHARS_POR_TOKEN

    return {
        "medido": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "raiz": str(raiz),
        "privado_presente": (raiz / "_PRIVADO").is_dir(),  # confirmado sin abrirlo
        "escala": {
            "notas": len(notas),
            "caracteres": chars,
            "tokens_wiki_aprox": tokens_wiki,
            "tokens_indice_aprox": tokens_indice,
            "factor_ahorro_indice": round(tokens_wiki / tokens_indice, 1) if tokens_indice else None,
            "tokens_por_nota_en_indice": round(tokens_indice / len(notas), 1) if notas else None,
        },
        "disciplina": {
            "frontmatter_completo": len(notas) - len(frontmatter_incompleto),
            "frontmatter_incompleto": frontmatter_incompleto,
            "indexadas": len(indexadas),
            "no_indexadas": sorted(set(por_nombre) - indexadas),
            "notas_vacias": vacias,
            "nombres_duplicados": sorted(set(duplicados)),
        },
        "esquema_areas": {
            "sin_area": sorted(sin_area),
            "area_invalida": area_invalida,
            "sin_tema": sorted(sin_tema),
            "temas_en_uso": dict(temas_en_uso.most_common()),
            "reparto_areas": dict(reparto_areas.most_common()),
            "areas_validas": sorted(AREAS_VALIDAS),
        },
        "grafo": {
            "enlaces_totales": total_enlaces,
            "media_por_nota": round(total_enlaces / len(notas), 1) if notas else 0,
            "sin_enlace_saliente": huerfanas_salida,
            "sin_enlace_entrante": huerfanas_entrada,
            "enlaces_rotos": {k: sorted(v) for k, v in sorted(rotos.items())},
            "transclusiones_rotas": transclusiones_rotas,
            "mas_enlazadas": entrantes.most_common(5),
        },
        "epistemico": {
            "notas_con_aviso": marcadas,
            "pct_notas_con_aviso": round(100 * marcadas / len(notas), 1) if notas else 0,
            "ocurrencias_sin_verificar": sin_verificar,
        },
        "higiene": {
            "notas_sueltas_en_raiz": sorted(sueltas),
            "subbovedas_anidadas_en_wiki": subbovedas,
        },
        "presupuesto_mapas": presupuesto_mapas(raiz),
        "tejido_faltante": tejido_faltante(
            temas_por_nota, {n: set(e) for n, e in salientes.items()}),
        "ingestion": censo_raw(raiz),
    }


# Techo de tokens de cada MAPA. Un mapa existe para poder decidir sin abrir lo
# que mapea; en cuanto cuesta como lo mapeado, deja de servir y nadie se entera.
#
# El 2026-07-28 se decidió jerarquizar "cuando el índice pase de ~10 000 tokens o
# el vault de ~150 notas"... y se escribió en prosa. El 2026-08-01 el vault tenía
# 181 notas y `alejandria/INDICE.md` **77 417 tokens** —8× el índice maestro— sin
# que saltara nada: el disparador estaba escrito y nadie lo comprobaba.
#
# Esto lo convierte en compuerta. Es el mismo movimiento que `claim_lint` hizo con
# las cifras infladas: de "hay que acordarse" a error de compilación.
PRESUPUESTO_MAPAS = {
    "index.md": 10_000,
    "index_TGDE.md": 12_000,
    "alejandria/INDICE.md": 2_000,
}
PRESUPUESTO_SUBCATALOGO = 12_000


def tejido_faltante(notas_meta: list[dict], enlaces: dict[str, set[str]],
                    tope: int = 12) -> list[dict]:
    """Pares de notas que comparten `tema:` y NO están enlazadas.

    Es la única parte del sistema que propone conocimiento nuevo en vez de
    verificarlo: dos notas que declaran el mismo tema y nunca se citaron son, casi
    siempre, un enlace que alguien no llegó a escribir. Un vault crece añadiendo
    notas; **se vuelve más inteligente añadiendo aristas** — y ese trabajo no lo
    hace nadie salvo que algo lo señale.

    Solo propone. Escribir el enlace exige leer las dos notas y decidir que la
    relación existe: eso es criterio, y el criterio no se automatiza aquí.
    """
    por_tema: dict[str, list[str]] = {}
    temas_de: dict[str, set[str]] = {}
    for n in notas_meta:
        ts = {t for t in n["temas"] if t}
        temas_de[n["nota"]] = ts
        for t in ts:
            por_tema.setdefault(t, []).append(n["nota"])

    candidatos: dict[tuple[str, str], set[str]] = {}
    for tema, miembros in por_tema.items():
        if len(miembros) > 25:      # un tema masivo no es señal de nada
            continue
        for i, a in enumerate(miembros):
            for b in miembros[i + 1:]:
                if b in enlaces.get(a, set()) or a in enlaces.get(b, set()):
                    continue
                candidatos.setdefault((a, b) if a < b else (b, a), set()).add(tema)

    filas = [
        {"a": a, "b": b, "temas": sorted(ts), "n": len(ts)}
        for (a, b), ts in candidatos.items() if len(ts) >= 2
    ]
    filas.sort(key=lambda f: (-f["n"], f["a"]))
    return filas[:tope]


def presupuesto_mapas(raiz: Path) -> dict:
    """¿Sigue siendo barato entrar por cada mapa? Ver PRESUPUESTO_MAPAS."""
    filas = []
    for rel, techo in PRESUPUESTO_MAPAS.items():
        p = raiz / rel
        if not p.is_file():
            continue
        tok = len(leer(p)) // CHARS_POR_TOKEN
        filas.append({"mapa": rel, "tokens": tok, "techo": techo,
                      "excede": tok > techo})
    # Los sub-catálogos de Alejandría son mapas de segundo nivel: si uno crece
    # demasiado, esa colección pide partirse en dos.
    for p in sorted((raiz / "alejandria").glob("INDICE_*.md")):
        tok = len(leer(p)) // CHARS_POR_TOKEN
        filas.append({"mapa": f"alejandria/{p.name}", "tokens": tok,
                      "techo": PRESUPUESTO_SUBCATALOGO,
                      "excede": tok > PRESUPUESTO_SUBCATALOGO})
    return {"filas": filas, "excedidos": [f for f in filas if f["excede"]]}


def censo_raw(raiz: Path) -> dict:
    """Cuenta raw/ SIN leer contenidos. Responde '¿qué se está perdiendo?'
    a nivel de censo, que es la pregunta que hoy no tiene respuesta."""
    base = raiz / "raw"
    if not base.is_dir():
        return {"presente": False}

    resumen: dict[str, dict] = {}
    for p in base.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(raiz)
        if _excluido(rel):
            continue
        # bandeja/notion/x/y.md -> "bandeja/notion"
        partes = p.relative_to(base).parts
        grupo = "/".join(partes[:2]) if len(partes) > 2 else (partes[0] if len(partes) > 1 else "(raíz)")
        d = resumen.setdefault(grupo, {"archivos": 0, "bytes": 0, "extensiones": Counter()})
        d["archivos"] += 1
        d["bytes"] += p.stat().st_size
        d["extensiones"][p.suffix.lower() or "(sin ext)"] += 1

    for d in resumen.values():
        d["extensiones"] = dict(d["extensiones"].most_common())

    en_bandeja = sum(v["archivos"] for k, v in resumen.items() if k.startswith("bandeja"))
    # Desde la reorganización de 2026-07-28 lo derivado NO vive en raw/: sale
    # hacia wiki/ (síntesis) o alejandria/ (texto íntegro). Contar solo raw/
    # daría siempre "100% sin digerir" y la métrica dejaría de informar.
    alej = raiz / "alejandria"
    derivados = len([p for p in alej.rglob("*") if p.is_file()]) if alej.is_dir() else 0
    total = en_bandeja + derivados
    return {
        "presente": True,
        "archivos_totales": total,
        "en_bandeja": en_bandeja,
        "derivados_en_alejandria": derivados,
        "pct_sin_digerir": round(100 * en_bandeja / total, 1) if total else 0,
        "por_grupo": dict(sorted(resumen.items())),
    }


def escribir_censo_csv(raiz: Path, destino: Path) -> int:
    """Inventario archivo por archivo de raw/bandeja/ — nombre, tamaño, fecha.
    Sin abrir ningún archivo: el censo dice QUÉ hay, no qué dice."""
    bandeja = raiz / "raw" / "bandeja"
    if not bandeja.is_dir():
        sys.exit(f"ERROR: no existe {bandeja}")
    filas = 0
    with destino.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ruta_relativa", "extension", "bytes", "modificado"])
        for p in sorted(bandeja.rglob("*")):
            if not p.is_file() or _excluido(p.relative_to(raiz)):
                continue
            st = p.stat()
            w.writerow([
                str(p.relative_to(raiz)),
                p.suffix.lower() or "(sin ext)",
                st.st_size,
                datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d"),
            ])
            filas += 1
    return filas


def a_markdown(m: dict) -> str:
    e, d, g, ep, h, i = (m["escala"], m["disciplina"], m["grafo"],
                         m["epistemico"], m["higiene"], m["ingestion"])
    ea = m["esquema_areas"]
    L = [
        f"# Métricas del vault — {m['medido'][:10]}",
        "",
        f"Generado por `vault_audit.py` sobre `{m['raiz']}`. **Cifras medidas, no estimadas.**",
        "⚠️ Mide forma, estructura y economía. **No verifica que el contenido sea cierto.**",
        "",
        "## Escala y economía de contexto",
        "",
        "| Métrica | Valor |",
        "| --- | --- |",
        f"| Notas en `wiki/` | {e['notas']} |",
        f"| Caracteres | {e['caracteres']:,} |",
        f"| Tokens si se cargara `wiki/` entero (≈, {CHARS_POR_TOKEN} chars/token) | ~{e['tokens_wiki_aprox']:,} |",
        # `index.md` MÁS sus sub-mapas: es lo que cuesta el mapa completo, no un
        # fichero. Lo que decide si entrar sigue siendo el techo POR fichero de
        # «Presupuesto de los mapas» — nadie carga el mapa entero de una vez, que
        # es justo el punto de haberlo partido.
        f"| Tokens del mapa completo (`index.md` + sub-mapas, ≈) | ~{e['tokens_indice_aprox']:,} |",
        f"| **Factor de ahorro de entrar por el índice** | **{e['factor_ahorro_indice']}×** |",
        f"| Coste del mapa por nota | {e['tokens_por_nota_en_indice']} tokens |",
        "",
        "## Disciplina formal",
        "",
        "| Métrica | Valor |",
        "| --- | --- |",
        f"| Frontmatter completo ({', '.join(CAMPOS_FRONTMATTER)}) | {d['frontmatter_completo']} / {e['notas']} |",
        f"| Indexadas en `index.md` | {d['indexadas']} / {e['notas']} |",
        f"| Notas vacías | {len(d['notas_vacias'])} |",
        f"| Nombres duplicados | {len(d['nombres_duplicados'])} |",
        "",
        "## Eje Área/Tema",
        "",
        "| Métrica | Valor |",
        "| --- | --- |",
        f"| Notas con `area:` | {e['notas'] - len(ea['sin_area'])} / {e['notas']} |",
        f"| Notas con `tema:` | {e['notas'] - len(ea['sin_tema'])} / {e['notas']} |",
        f"| **Áreas fuera del vocabulario** | **{len(ea['area_invalida'])}** |",
        f"| Temas distintos en uso | {len(ea['temas_en_uso'])} |",
        "",
        "Reparto por Área (una nota puede declarar varias):",
        "",
        "| Área | Notas |",
        "| --- | ---: |",
        *[f"| {k} | {v} |" for k, v in sorted(ea["reparto_areas"].items(),
                                              key=lambda x: -x[1])],
        "",
        "## Grafo de enlaces",
        "",
        "| Métrica | Valor |",
        "| --- | --- |",
        f"| Enlaces `[[ ]]` | {g['enlaces_totales']} (media {g['media_por_nota']}/nota) |",
        f"| Sin enlace saliente (islas) | {len(g['sin_enlace_saliente'])} |",
        f"| Sin enlace entrante (sin backlinks) | {len(g['sin_enlace_entrante'])} |",
        f"| **Enlaces rotos** | **{len(g['enlaces_rotos'])}** |",
        f"| Transclusiones rotas | {len(g['transclusiones_rotas'])} |",
        "",
        "## Presupuesto de los mapas",
        "",
        "Un mapa existe para decidir **sin** abrir lo que mapea. Si cuesta como lo",
        "mapeado, deja de servir — y crece en silencio.",
        "",
        "| Mapa | Tokens | Techo | |",
        "| --- | ---: | ---: | --- |",
        *[f"| `{x['mapa']}` | ~{x['tokens']:,} | {x['techo']:,} | "
          f"{'🛑 **PARTIR**' if x['excede'] else '✅'} |"
          for x in m["presupuesto_mapas"]["filas"]],
        "",
        "## Tejido faltante — aristas que el grafo pide y nadie escribió",
        "",
        "Notas que **declaran los mismos temas y nunca se citaron**. Un vault crece",
        "añadiendo notas; se vuelve más inteligente añadiendo **aristas**. Esto solo",
        "propone: escribir el enlace exige leer las dos y decidir que la relación",
        "existe, y eso es criterio.",
        "",
        *([f"| Nota A | Nota B | Temas compartidos |", "| --- | --- | --- |"]
          + [f"| [[{x['a']}]] | [[{x['b']}]] | {', '.join(x['temas'])} |"
             for x in m["tejido_faltante"]]
          if m["tejido_faltante"] else ["_Sin candidatos: el tejido está al día._"]),
        "",
        "## Honestidad epistémica",
        "",
        "| Métrica | Valor |",
        "| --- | --- |",
        f"| Notas con `⚠️` | {ep['notas_con_aviso']} / {e['notas']} ({ep['pct_notas_con_aviso']}%) |",
        f"| Ocurrencias de \"sin verificar\" | {ep['ocurrencias_sin_verificar']} |",
        "",
        "## Higiene estructural",
        "",
        f"- Notas sueltas en la raíz: {len(h['notas_sueltas_en_raiz'])} {h['notas_sueltas_en_raiz'] or ''}",
        f"- Sub-bóvedas `.obsidian` anidadas dentro de `wiki/`: {len(h['subbovedas_anidadas_en_wiki'])} {h['subbovedas_anidadas_en_wiki'] or ''}",
        "",
    ]
    if g["enlaces_rotos"]:
        L += ["### Enlaces rotos (destino → citado desde)", "",
              "| Destino | Citado desde |", "| --- | --- |"]
        L += [f"| `{k}` | {', '.join(v)} |" for k, v in g["enlaces_rotos"].items()]
        L += [""]
    if d["frontmatter_incompleto"]:
        L += ["### Frontmatter incompleto", "",
              "| Nota | Campos que faltan |", "| --- | --- |"]
        L += [f"| {x['nota']} | {', '.join(x['faltan'])} |" for x in d["frontmatter_incompleto"]]
        L += [""]
    if d["no_indexadas"]:
        L += ["### No indexadas en `index.md`", ""]
        L += [f"- {n}" for n in d["no_indexadas"]] + [""]

    if i.get("presente"):
        L += ["## Ingestión (`raw/`)", "",
              "| Métrica | Valor |", "| --- | --- |",
              f"| Archivos totales | {i['archivos_totales']:,} |",
              f"| En `bandeja/` (sin digerir) | {i['en_bandeja']:,} |",
              f"| Derivados a `alejandria/` | {i['derivados_en_alejandria']:,} |",
              f"| **% sin digerir** | **{i['pct_sin_digerir']}%** |", "",
              "| Grupo | Archivos | MB | Extensiones |", "| --- | --- | --- | --- |"]
        for grupo, v in i["por_grupo"].items():
            exts = ", ".join(f"{k} {n}" for k, n in list(v["extensiones"].items())[:4])
            L.append(f"| `{grupo}` | {v['archivos']:,} | {v['bytes']/1e6:.1f} | {exts} |")
        L += [""]
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("raiz", type=Path)
    ap.add_argument("--json", type=Path, help="volcar las métricas crudas")
    ap.add_argument("--md", type=Path, help="volcar el reporte en Markdown")
    ap.add_argument("--censo-raw", type=Path, help="CSV con el inventario de raw/bandeja/")
    ap.add_argument("--ci", action="store_true",
                    help="sale con código 1 si se viola algún invariante duro")
    args = ap.parse_args()

    raiz = args.raiz.resolve()
    m = medir(raiz)

    if args.censo_raw:
        n = escribir_censo_csv(raiz, args.censo_raw)
        print(f"censo: {n} archivos -> {args.censo_raw}")
    if args.json:
        args.json.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"json  -> {args.json}")
    if args.ci:
        # Invariantes duros: cada uno se pagó con un fallo real, no son gustos.
        d, g, h, e = m["disciplina"], m["grafo"], m["higiene"], m["escala"]
        fallos = []
        if g["enlaces_rotos"]:
            fallos.append(f"{len(g['enlaces_rotos'])} enlaces rotos: {sorted(g['enlaces_rotos'])[:5]}")
        if g["transclusiones_rotas"]:
            fallos.append(f"{len(g['transclusiones_rotas'])} transclusiones rotas")
        if d["frontmatter_incompleto"]:
            fallos.append(f"{len(d['frontmatter_incompleto'])} notas sin frontmatter completo: "
                          f"{[x['nota'] for x in d['frontmatter_incompleto'][:5]]}")
        if d["no_indexadas"]:
            fallos.append(f"{len(d['no_indexadas'])} notas no indexadas: {d['no_indexadas'][:5]}")
        if d["notas_vacias"]:
            fallos.append(f"notas vacías: {d['notas_vacias']}")
        if d["nombres_duplicados"]:
            fallos.append(f"nombres duplicados: {d['nombres_duplicados']}")
        if g["sin_enlace_saliente"]:
            fallos.append(f"notas isla: {g['sin_enlace_saliente'][:5]}")
        if h["subbovedas_anidadas_en_wiki"]:
            fallos.append(f"sub-bóvedas anidadas: {h['subbovedas_anidadas_en_wiki']}")
        if h["notas_sueltas_en_raiz"]:
            fallos.append(f"notas sueltas en la raíz: {h['notas_sueltas_en_raiz']}")
        # Eje Área/Tema: un área fuera del vocabulario hace que la nota
        # desaparezca de las consultas Dataview sin error visible. Es fallo duro.
        ea = m["esquema_areas"]
        if ea["area_invalida"]:
            fallos.append(f"{len(ea['area_invalida'])} notas con área fuera del vocabulario: "
                          f"{[(x['nota'], x['areas']) for x in ea['area_invalida'][:5]]}")
        if ea["sin_area"]:
            fallos.append(f"{len(ea['sin_area'])} notas sin `area:`: {ea['sin_area'][:5]}")
        if ea["sin_tema"]:
            fallos.append(f"{len(ea['sin_tema'])} notas sin `tema:`: {ea['sin_tema'][:5]}")
        for f_ in fallos:
            print(f"  FALLO: {f_}")
        if fallos:
            sys.exit(1)
        print(f"  OK: {e['notas']} notas, {g['enlaces_totales']} enlaces, "
              f"0 rotos, frontmatter e índice al 100%, "
              f"área/tema en {e['notas']}/{e['notas']}")
        # Presupuesto de los mapas: AVISO, no fallo. Un mapa gordo no hace que el
        # vault sea incorrecto, lo hace caro — y partir una colección es una
        # decisión de curación, no un arreglo mecánico. Pero se dice en voz alta
        # en cada corrida: el fallo del 2026-08-01 fue justo que nadie lo miraba.
        for x in m["presupuesto_mapas"]["excedidos"]:
            print(f"  AVISO: `{x['mapa']}` cuesta ~{x['tokens']:,} tokens "
                  f"(techo {x['techo']:,}) — pide partirse. No bloquea.")
        sys.exit(0)

    reporte = a_markdown(m)
    if args.md:
        args.md.write_text(reporte, encoding="utf-8")
        print(f"md    -> {args.md}")
    else:
        print(reporte)


if __name__ == "__main__":
    main()
