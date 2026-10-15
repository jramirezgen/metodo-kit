#!/usr/bin/env python3
"""
notion_sync.py — censo del workspace de Notion y diff contra lo que hay en disco.

`notion_fetch.py` solo rellena huecos conocidos (los marcadores
`_(destino fuera del volcado: <uuid>)_`). Este script hace la pregunta
completa: **¿qué existe en Notion que no esté en `raw/`?**

Enumera todo el workspace con `/v1/search` (páginas y bases de datos), lo
compara con los `notion_id:` presentes en el vault, y baja lo que falte
reutilizando el renderizador de `notion_fetch.py`.

Uso:
    python3 notion_sync.py <VAULT> --token-file <ruta> [--censo | --bajar]

    --censo   solo mide y reporta (por defecto)
    --bajar   además descarga lo ausente a raw/bandeja/notion/_sync_<fecha>/
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from notion_fetch import _pedir, _bloques, a_markdown, _titulo_de  # noqa: E402

HOY = date.today().isoformat()


def censo_remoto(token: str, cache: Path | None = None) -> list[dict]:
    """Todo lo que la integración puede ver en el workspace.

    El censo cuesta ~45 barridos de 100 y no cambia entre reintentos de la
    misma sesión, así que se cachea: un `--bajar` que se corte debe poder
    reanudarse sin volver a preguntarle al workspace entero.
    """
    if cache and cache.exists():
        print(f"  (censo cacheado: {cache})", file=sys.stderr)
        return json.loads(cache.read_text(encoding="utf-8"))
    objetos, cursor = [], None
    while True:
        cuerpo = {"page_size": 100}
        if cursor:
            cuerpo["start_cursor"] = cursor
        d = _pedir("/search", token, "POST", cuerpo)
        if d.get("object") == "error":
            print(f"✗ /search: {d.get('status')} {d.get('code')}", file=sys.stderr)
            break
        objetos.extend(d.get("results", []))
        print(f"  …{len(objetos)} objetos", end="\r", file=sys.stderr)
        if not d.get("has_more"):
            break
        cursor = d["next_cursor"]
        time.sleep(0.34)
    print(file=sys.stderr)
    if cache:
        cache.write_text(json.dumps(objetos), encoding="utf-8")
    return objetos


def descubrir_ocultos(vault: Path, token: str, remotos: list[dict],
                      limite: int | None = None) -> dict[str, list[str]]:
    """Bases de datos que `/v1/search` NO devuelve.

    Comprobado el 2026-07-30: la base `Facturaciones`
    (`23bbb61a-ec77-801f-9cb8-ed1016dc95f5`) no aparece en `/v1/search`, pero
    `GET /databases/{id}` responde 200 y tiene 2 filas. O sea que **el censo por
    búsqueda es una cota inferior, no el total**.

    Las bases visibles sí traen sus filas completas (medido: 1 207 filas en las
    primeras 50, ninguna ausente del search). La fuga son bases enteras
    invisibles, y a esas solo se llega **caminando los bloques** de las páginas
    conocidas y recogiendo los `child_database`.
    """
    vistos = {o["id"].replace("-", "") for o in remotos}
    paginas = [o["id"] for o in remotos if o["object"] == "page"][:limite]
    ocultas: dict[str, list[str]] = {}

    for i, pid in enumerate(paginas, 1):
        for b in _bloques(pid, token, prof=4):     # prof=4 => solo el nivel 1
            if b.get("type") != "child_database":
                continue
            did = b["id"]
            if did.replace("-", "") in vistos:
                continue
            ocultas.setdefault(did, []).append(pid)
        if i % 100 == 0:
            print(f"  descubrimiento {i}/{len(paginas)} · ocultas {len(ocultas)}",
                  file=sys.stderr, flush=True)
        time.sleep(0.34)
    return ocultas


def filas_de(did: str, token: str) -> list[dict]:
    """Filas de una base, paginadas."""
    salida, cursor = [], None
    while True:
        cuerpo = {"page_size": 100}
        if cursor:
            cuerpo["start_cursor"] = cursor
        d = _pedir(f"/databases/{did}/query", token, "POST", cuerpo)
        if d.get("object") == "error":
            return salida
        salida.extend(d.get("results", []))
        if not d.get("has_more"):
            return salida
        cursor = d["next_cursor"]
        time.sleep(0.34)


def ids_locales(vault: Path) -> set[str]:
    ids = set()
    for md in (vault / "raw").rglob("*.md"):
        m = re.search(r"^notion_id:\s*(\S+)", md.read_text(encoding="utf-8", errors="ignore"), re.M)
        if m:
            ids.add(m.group(1).strip().lower())
    return ids


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("vault", type=Path)
    ap.add_argument("--token-file", type=Path, required=True)
    ap.add_argument("--bajar", action="store_true")
    ap.add_argument("--cache", type=Path, help="JSON donde cachear el censo")
    ap.add_argument("--excluir", action="append", default=[],
                    help="título exacto a NO bajar; repetible. Ej: --excluir 'Daily Habits'")
    ap.add_argument("--salida", type=Path, help="carpeta destino (por defecto _sync_<fecha>)")
    ap.add_argument("--descubrir", type=int, metavar="N", nargs="?", const=0,
                    help="camina los bloques de N páginas (0 = todas) buscando bases "
                         "que /v1/search no devuelve, y baja sus filas")
    a = ap.parse_args()

    token = a.token_file.read_text(encoding="utf-8").strip()

    print("Censando el workspace de Notion…", file=sys.stderr)
    remotos = censo_remoto(token, a.cache)
    locales = ids_locales(a.vault)

    faltan = [o for o in remotos if o["id"].lower() not in locales]
    tipos = Counter(o["object"] for o in remotos)
    archivadas = sum(1 for o in faltan if o.get("archived") or o.get("in_trash"))

    print(f"\n{'='*66}")
    print(f"En Notion (visible por la integración) : {len(remotos)}  {dict(tipos)}")
    print(f"Ya en disco (`notion_id:` en raw/)     : {len(locales)}")
    print(f"AUSENTES en disco                      : {len(faltan)}")
    print(f"  de ellas archivadas/en papelera      : {archivadas}")
    print(f"{'='*66}\n")

    if faltan:
        print("Ausentes (título · tipo · última edición):")
        for o in sorted(faltan, key=lambda x: x.get("last_edited_time", ""), reverse=True)[:60]:
            marca = "🗑️ " if (o.get("archived") or o.get("in_trash")) else "   "
            print(f"  {marca}{_titulo_de(o)[:56]:58} {o['object']:9} {o.get('last_edited_time','')[:10]}")
        if len(faltan) > 60:
            print(f"  … y {len(faltan)-60} más")

    if a.descubrir is not None:
        lim = a.descubrir or None
        print(f"\nDescubriendo bases invisibles a /v1/search "
              f"(caminando {lim or 'todas las'} páginas)…", file=sys.stderr)
        ocultas = descubrir_ocultos(a.vault, token, remotos, lim)
        print(f"\n{'='*66}")
        print(f"BASES QUE /v1/search NO DEVUELVE: {len(ocultas)}")
        print(f"{'='*66}")
        destino = a.salida or (a.vault / "raw" / "bandeja" / "notion" / f"_ocultas_{HOY}")
        total_filas = 0
        for did, padres in ocultas.items():
            meta = _pedir(f"/databases/{did}", token)
            nombre = _titulo_de(meta) if meta.get("object") == "database" else "sin-titulo"
            filas = filas_de(did, token)
            total_filas += len(filas)
            print(f"  {nombre[:48]:50} {len(filas):4} filas  (en {len(padres)} pág.)")
            if not filas or not a.bajar:
                continue
            destino.mkdir(parents=True, exist_ok=True)
            for f in filas:
                if f["id"].lower() in locales:
                    continue
                nom, txt = a_markdown(f, _bloques(f["id"], token))
                base, n = nom, 1
                while (destino / f"{nom}.md").exists():
                    n += 1
                    nom = f"{base}-{n}"
                (destino / f"{nom}.md").write_text(txt, encoding="utf-8")
                time.sleep(0.34)
        print(f"\nFilas en bases ocultas: {total_filas}"
              + (f" — bajadas a {destino}" if a.bajar else " (usa --bajar para traerlas)"))
        return 0

    if not a.bajar or not faltan:
        return 0

    destino = a.salida or (a.vault / "raw" / "bandeja" / "notion" / f"_sync_{HOY}")
    destino.mkdir(parents=True, exist_ok=True)

    excluidos = {e.casefold() for e in a.excluir}
    cola = [o for o in faltan
            if not (o.get("archived") or o.get("in_trash"))       # la papelera no es conocimiento
            and _titulo_de(o).casefold() not in excluidos]
    print(f"\nCola: {len(cola)}  (excluidos por título: {len(faltan)-len(cola)})")

    # Reanudable: un `notion_id:` ya escrito en el destino no se vuelve a pedir.
    hechos = set()
    for md in destino.glob("*.md"):
        m = re.search(r"^notion_id:\s*(\S+)", md.read_text(encoding="utf-8", errors="ignore"), re.M)
        if m:
            hechos.add(m.group(1).strip().lower())
    if hechos:
        print(f"Reanudando: {len(hechos)} ya estaban bajadas.")

    ok, fallos = 0, 0
    for i, o in enumerate(cola, 1):
        if o["id"].lower() in hechos:
            continue
        try:
            nombre, texto = a_markdown(o, _bloques(o["id"], token))
        except Exception as e:                      # una página rota no aborta el barrido
            fallos += 1
            print(f"[{i}/{len(cola)}] ✗ {o['id']}: {e}")
            continue
        base, n = nombre, 1
        while (destino / f"{nombre}.md").exists():
            n += 1
            nombre = f"{base}-{n}"
        (destino / f"{nombre}.md").write_text(texto, encoding="utf-8")
        ok += 1
        if ok % 25 == 0 or len(texto) > 20000:
            print(f"[{i}/{len(cola)}] ✓ {ok} bajadas · última: {nombre[:50]} ({len(texto)} B)", flush=True)
        time.sleep(0.34)

    print(f"\nBajadas {ok} páginas nuevas, {fallos} fallos.")
    (destino / "_CENSO.json").write_text(
        json.dumps({"fecha": HOY, "remotos": len(remotos), "locales": len(locales),
                    "ausentes": len(faltan), "en_cola": len(cola),
                    "excluidos": a.excluir, "bajadas": ok, "fallos": fallos}, indent=2),
        encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
