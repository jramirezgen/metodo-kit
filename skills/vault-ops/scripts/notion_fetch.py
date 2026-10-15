#!/usr/bin/env python3
"""
notion_fetch.py — completa el volcado de Notion del vault.

El volcado del 2026-07-26 dejó referencias colgando: cuando una página
enlazaba a otra que el barrido no había capturado, se escribió el marcador
`_(destino fuera del volcado: <uuid>)_` en vez del wikilink. Este script
localiza esos UUIDs huérfanos, los baja por la API y los escribe con el
mismo formato que el resto del volcado, de modo que los marcadores se
puedan reescribir como wikilinks navegables.

Uso:
    python3 notion_fetch.py <VAULT> --token-file <ruta> [--salida <dir>]
    python3 notion_fetch.py <VAULT> --token-file <ruta> --solo-listar

El token NUNCA se imprime ni se escribe a disco por este script.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# El marcador que dejó el volcado incompleto del 2026-07-26.
RE_HUERFANO = re.compile(r"fuera del volcado: `([0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12})`")
RE_ILEGAL = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


# ─────────────────────────── API ───────────────────────────

def _pedir(ruta: str, token: str, metodo: str = "GET", cuerpo: dict | None = None) -> dict:
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(f"{API}{ruta}", data=datos, method=metodo)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Notion-Version", NOTION_VERSION)
    if datos:
        req.add_header("Content-Type", "application/json")
    for intento in range(5):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            # 429 = rate limit, 5xx = transitorio. El resto se propaga como dato.
            if e.code == 429 or e.code >= 500:
                time.sleep(float(e.headers.get("Retry-After", 2)) * (intento + 1))
                continue
            return {"object": "error", "status": e.code, "code": e.reason}
        except (urllib.error.URLError, TimeoutError) as e:
            time.sleep(2 * (intento + 1))
            ultimo = str(e)
    return {"object": "error", "status": 0, "code": "sin respuesta tras 5 intentos"}


def _bloques(bid: str, token: str, prof: int = 0) -> list[dict]:
    """Descarga los hijos de un bloque, recursivamente."""
    if prof > 4:
        return []
    salida, cursor = [], None
    while True:
        ruta = f"/blocks/{bid}/children?page_size=100"
        if cursor:
            ruta += f"&start_cursor={cursor}"
        d = _pedir(ruta, token)
        if d.get("object") == "error":
            return salida
        for b in d.get("results", []):
            if b.get("has_children") and b.get("type") != "child_page":
                b["_hijos"] = _bloques(b["id"], token, prof + 1)
            salida.append(b)
        if not d.get("has_more"):
            return salida
        cursor = d["next_cursor"]


# ─────────────────────── Render a Markdown ───────────────────────

def _texto(rich: list[dict]) -> str:
    partes = []
    for t in rich or []:
        s = t.get("plain_text", "")
        a = t.get("annotations", {})
        if a.get("code"):
            s = f"`{s}`"
        if a.get("bold"):
            s = f"**{s}**"
        if a.get("italic"):
            s = f"_{s}_"
        if t.get("href"):
            s = f"[{s}]({t['href']})"
        partes.append(s)
    return "".join(partes)


_PREFIJO = {
    "heading_1": "# ", "heading_2": "## ", "heading_3": "### ",
    "bulleted_list_item": "- ", "numbered_list_item": "1. ",
    "quote": "> ", "to_do": "- [ ] ", "callout": "> ",
}


def _render(bloques: list[dict], nivel: int = 0) -> list[str]:
    lineas = []
    sangria = "  " * nivel
    for b in bloques:
        t = b.get("type", "")
        cont = b.get(t, {}) or {}
        rich = cont.get("rich_text", [])
        if t == "code":
            lineas.append(f"{sangria}```{cont.get('language','')}")
            lineas.append(_texto(rich))
            lineas.append(f"{sangria}```")
        elif t == "divider":
            lineas.append(f"{sangria}---")
        elif t in ("image", "file", "pdf"):
            url = (cont.get("file") or cont.get("external") or {}).get("url", "")
            lineas.append(f"{sangria}![]({url})")
        elif t == "child_page":
            lineas.append(f"{sangria}- [[{_slug(cont.get('title','sin-titulo'))}]]")
        elif t == "child_database":
            # El ID es obligatorio aquí: `/v1/search` NO devuelve todas las bases
            # anidadas (comprobado el 2026-07-30 con `Facturaciones`, invisible a
            # search pero accesible por GET directo y con 2 filas). Sin el ID, un
            # volcado no deja rastro de la base que se perdió.
            lineas.append(f"{sangria}- (base de datos) {cont.get('title','Untitled')} "
                          f"`db:{b.get('id','?')}`")
        elif t == "table_row":
            celdas = [_texto(c) for c in cont.get("cells", [])]
            lineas.append(f"{sangria}| " + " | ".join(celdas) + " |")
        elif rich:
            if t == "to_do" and cont.get("checked"):
                lineas.append(f"{sangria}- [x] {_texto(rich)}")
            else:
                lineas.append(f"{sangria}{_PREFIJO.get(t,'')}{_texto(rich)}")
        if b.get("_hijos"):
            lineas.extend(_render(b["_hijos"], nivel + 1))
    return lineas


def _valor_prop(p: dict) -> str:
    """Aplana el VALOR de una propiedad de página a texto. Las relaciones se
    cuentan, igual que hizo el volcado original.

    ⚠️ Solo vale para páginas. En un objeto `database`, `properties` es el
    ESQUEMA y la misma clave tiene otra forma —`multi_select` es
    `{"options": [...]}` en vez de una lista—, así que iterarlo devuelve
    strings y revienta. Esa fue la causa de los 162 fallos del sync del
    2026-07-30; ahora las bases van por `_esquema_prop()`.
    """
    t = p.get("type")
    if t == "title" or t == "rich_text":
        v = p.get(t, [])
        return _texto(v) if isinstance(v, list) else ""
    if t == "select":
        v = p.get("select")
        return v.get("name", "") if isinstance(v, dict) else ""
    if t == "multi_select":
        v = p.get("multi_select", [])
        if not isinstance(v, list):
            return ""
        return ", ".join(s.get("name", "") for s in v if isinstance(s, dict))
    if t == "relation":
        v = p.get("relation", [])
        return f"{len(v)} vinculo(s)" if isinstance(v, list) else ""
    if t in ("number", "checkbox", "url", "email", "phone_number"):
        return str(p.get(t, ""))
    if t == "date":
        d = p.get("date") or {}
        return d.get("start", "")
    if t in ("created_time", "last_edited_time"):
        return p.get(t, "")
    if t == "people":
        v = p.get("people", [])
        if not isinstance(v, list):
            return ""
        return ", ".join(x.get("name", "") for x in v if isinstance(x, dict))
    if t == "status":
        v = p.get("status")
        return v.get("name", "") if isinstance(v, dict) else ""
    if t == "formula":
        f = p.get("formula")
        return str(f.get(f.get("type"), "")) if isinstance(f, dict) else ""
    return ""


def _esquema_prop(nombre: str, p: dict) -> str:
    """Describe una propiedad del ESQUEMA de una base (no su valor).

    En una base lo informativo no es "qué vale" —no vale nada, es una
    definición— sino "qué campos tiene y de qué tipo", incluidas las opciones
    de un select.
    """
    t = p.get("type", "?")
    if t in ("select", "multi_select", "status"):
        cfg = p.get(t)
        opciones = (cfg or {}).get("options", []) if isinstance(cfg, dict) else []
        nombres = [o.get("name", "") for o in opciones if isinstance(o, dict)]
        if nombres:
            return f"{t}: {', '.join(nombres[:12])}"
    return t


def _slug(titulo: str) -> str:
    s = RE_ILEGAL.sub("", titulo).strip().rstrip(".")
    return (s or "sin-titulo")[:70]


def _titulo_de(pagina: dict) -> str:
    for p in (pagina.get("properties") or {}).values():
        if p.get("type") == "title":
            return _texto(p.get("title", [])) or "sin-titulo"
    tt = pagina.get("title")
    return _texto(tt) if tt else "sin-titulo"


def a_markdown(pagina: dict, bloques: list[dict]) -> tuple[str, str]:
    titulo = _titulo_de(pagina)
    es_db = pagina.get("object") == "database"
    fm = [
        "---",
        "origen: notion",
        f"tipo: {'database' if es_db else 'page'}",
        f'titulo: "{titulo}"',
        f"notion_id: {pagina.get('id','')}",
        f"url: {pagina.get('url','')}",
        f"creado: {pagina.get('created_time','')}",
        f"editado: {pagina.get('last_edited_time','')}",
        "recuperado: 2026-07-30  # notion_fetch.py, completado del volcado del 26-jul",
    ]
    for nombre, p in (pagina.get("properties") or {}).items():
        if not isinstance(p, dict) or p.get("type") == "title":
            continue
        # Una base define su esquema; una página lleva valores. No se mezclan.
        v = _esquema_prop(nombre, p) if es_db else _valor_prop(p)
        if v:
            clave = re.sub(r"\W+", "_", nombre).strip("_")
            fm.append(f'{"col" if es_db else "prop"}_{clave}: "{v}"')
    fm.append("---")
    cuerpo = [f"\n# {titulo}\n"] + _render(bloques)
    return _slug(titulo), "\n".join(fm) + "\n".join(cuerpo) + "\n"


# ─────────────────────────── Orquestación ───────────────────────────

def huerfanos(vault: Path) -> dict[str, list[str]]:
    """UUID -> archivos que lo referencian."""
    encontrados: dict[str, list[str]] = {}
    raw = vault / "raw"
    for md in raw.rglob("*.md"):
        try:
            txt = md.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for uid in RE_HUERFANO.findall(txt):
            encontrados.setdefault(uid, []).append(str(md.relative_to(vault)))
    # Ya presentes en el volcado -> no son huérfanos de verdad.
    ya = set()
    for md in raw.rglob("*.md"):
        m = re.search(r"^notion_id:\s*(\S+)", md.read_text(encoding="utf-8", errors="ignore"), re.M)
        if m:
            ya.add(m.group(1).strip())
    return {k: v for k, v in encontrados.items() if k not in ya}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vault", type=Path)
    ap.add_argument("--token-file", type=Path, required=True)
    ap.add_argument("--salida", default="raw/bandeja/notion/_recuperado_2026-07-30")
    ap.add_argument("--solo-listar", action="store_true")
    a = ap.parse_args()

    pend = huerfanos(a.vault)
    print(f"UUIDs huérfanos: {len(pend)}")
    if a.solo_listar:
        for uid, refs in sorted(pend.items()):
            print(f"  {uid}  <- {len(refs)} ref(s): {refs[0]}")
        return 0
    if not pend:
        print("Nada que recuperar.")
        return 0

    token = a.token_file.read_text(encoding="utf-8").strip()
    destino = a.vault / a.salida
    destino.mkdir(parents=True, exist_ok=True)

    ok, fallos, usados = 0, {}, set()
    for i, uid in enumerate(sorted(pend), 1):
        pag = _pedir(f"/pages/{uid}", token)
        if pag.get("object") == "error":
            pag = _pedir(f"/databases/{uid}", token)
        if pag.get("object") == "error":
            fallos[uid] = f"{pag.get('status')} {pag.get('code')}"
            print(f"[{i}/{len(pend)}] {uid}  ✗ {fallos[uid]}")
            continue
        nombre, texto = a_markdown(pag, _bloques(uid, token))
        # El vault vive en `F:` (drvfs), que NO distingue mayúsculas: Notion sí
        # permite dos páginas "Finanzas Personales" y "Finanzas personales", y
        # sin esto la segunda pisa a la primera en silencio.
        base = nombre
        n = 1
        while nombre.casefold() in usados or (destino / f"{nombre}.md").exists():
            n += 1
            nombre = f"{base}-{n}"
        usados.add(nombre.casefold())
        (destino / f"{nombre}.md").write_text(texto, encoding="utf-8")
        ok += 1
        print(f"[{i}/{len(pend)}] {uid}  ✓ {nombre}.md ({len(texto)} B)")
        time.sleep(0.34)  # Notion limita a ~3 req/s

    print(f"\nRecuperadas {ok}/{len(pend)} en {a.salida}")
    if fallos:
        print(f"Fallaron {len(fallos)}:")
        for uid, err in fallos.items():
            print(f"  {uid}: {err}")
        (destino / "_FALLOS.json").write_text(json.dumps(fallos, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
