# -*- coding: utf-8 -*-
"""Audita la wiki corporativa de un repo. Sale 0 si pasa, 1 si hay fallos duros.

    python3 auditar.py <repo>

Duros (solo para nodos CERRADOS en el registro): archivo ausente · marcador POR COMPLETAR · sección ausente, vacía o
con solo «pendiente»/TODO (mínimo de palabras) · tabla con celdas vacías · en el dossier (BP98), ⚠️ o notas internas.
Duros siempre: patrones de identidad en docs/ y registro/ (DNI, correo, móvil, «nombre:») y cifras tecleadas en .m/.R/.r.
Este archivo se VENDORIZA como plan/auditar_empresa.py (lee el catálogo de plan/nodos_empresa.py si existe).
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

MIN_PALABRAS = 12
QUI = Path(__file__).resolve()
CAT_SKILL = QUI.parent.parent / "catalogo" / "capitulos.json"
# INC-064: sólo se exime una fecha AAAAMMDD VÁLIDA del siglo XXI (mes 01-12, día 01-31); antes se eximía todo número que empezara por 20.
PII = [(re.compile(r"(?<![0-9])(?!20[0-9]{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01])(?![0-9]))[0-9]{8}(?![0-9])"),
        "número de 8 dígitos (¿DNI?)"),
       (re.compile(r"(?<![0-9])9[0-9]{2}[ .-][0-9]{3}[ .-][0-9]{3}(?![0-9])"), "teléfono con separadores"),
       (re.compile(r"\+51[\s0-9-]{8,}"), "teléfono +51"),
       (re.compile(r"[\w.+-]+\s?(?:@|\[at\]|\(at\))\s?[\w-]+\.[\w.-]+", re.I), "correo"),
       (re.compile(r"(?<![0-9])9[0-9]{8}(?![0-9])"), "móvil de 9 dígitos"),
       (re.compile(r"^\s*(?:nombre|apellidos?|dni|paciente)\s*:\s*\S+", re.I | re.M), "campo de identidad rellenado")]
PLACEHOLDER = re.compile(r"_\(pendiente\)_|\bTODO\b|\bpor definir\b|\bpendiente\b\s*$", re.I | re.M)


def catalogo(repo: Path) -> list[dict]:
    mod = repo / "plan" / "nodos_empresa.py"
    if mod.exists():
        spec = importlib.util.spec_from_file_location("nodos_empresa", mod)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m.CATALOGO["nodos"]
    return json.loads(CAT_SKILL.read_text(encoding="utf-8"))["nodos"]


def cerrados(repo: Path) -> set[str]:
    reg = repo / "registro" / "nodos.jsonl"
    est = {}
    if reg.exists():
        for ln in reg.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                d = json.loads(ln)
                est[d["nodo"]] = d["estado"]
    return {k for k, v in est.items() if v in ("hecho", "juzgado")}


def secciones(t: str) -> dict[str, str]:
    """Encabezado (sin numeración) -> cuerpo hasta el siguiente encabezado."""
    partes = re.split(r"^(#+\s.*)$", t, flags=re.M)
    out = {}
    for i in range(1, len(partes) - 1, 2):
        nombre = re.sub(r"^#+\s*(?:[0-9]+(?:·\w+)?\.?\s+)?", "", partes[i]).strip()
        nivel = len(partes[i]) - len(partes[i].lstrip("#"))
        cuerpo = partes[i + 1]
        # una sección incluye sus subsecciones (encabezados de nivel mayor) hasta el siguiente encabezado de su nivel o menor
        for j in range(i + 2, len(partes) - 1, 2):
            if len(partes[j]) - len(partes[j].lstrip("#")) <= nivel:
                break
            cuerpo += partes[j] + partes[j + 1]
        out[nombre] = cuerpo
    return out


def palabras(cuerpo: str) -> int:
    return len(re.findall(r"\w+", PLACEHOLDER.sub("", cuerpo)))


def sin_cifras(codigo: str) -> str:
    """Quita cadenas y comentarios antes de buscar cifras tecleadas."""
    sin_str = re.sub(r"'[^']*'|\"[^\"]*\"", "''", codigo)
    return re.split(r"%|#", sin_str)[0]


def auditar(repo: Path) -> tuple[list[str], list[str]]:
    duros, avisos = [], []
    cat = catalogo(repo)
    cerr = cerrados(repo)
    for c in cat:
        if not c["entrega"].endswith(".md"):
            continue
        ruta = (repo / "docs" / "empresa" / c["entrega"]) if c["entrega_base"] == "empresa" else (repo / c["entrega"])
        cerrado = c["id"] in cerr
        if not ruta.exists():
            if cerrado:
                duros.append(f"{c['id']} está cerrado pero no existe {ruta.relative_to(repo)}")
            continue
        t = ruta.read_text(encoding="utf-8")
        if not cerrado:
            if not re.search(r"POR COMPLETAR", t, re.I):
                avisos.append(f"{c['id']}: sin marcador POR COMPLETAR y sin cerrar (¿falta registrar?)")
            continue
        if re.search(r"POR COMPLETAR", t, re.I):
            duros.append(f"{c['id']} está cerrado pero {ruta.name} conserva POR COMPLETAR")
        sec = secciones(t)
        for s in c["secciones"]:
            clave = next((k for k in sec if k.startswith(s)), None)
            if clave is None:
                duros.append(f"{c['id']}: falta la sección «{s}»")
            elif palabras(sec[clave]) < MIN_PALABRAS:
                duros.append(f"{c['id']}: la sección «{s}» está vacía o es solo un marcador (<{MIN_PALABRAS} palabras)")
        if re.search(r"\|[ \t]*\|", re.sub(r"^\|[-:| \t]+\|[ \t]*$", "", t, flags=re.M)):
            duros.append(f"{c['id']}: tabla con celdas vacías")
        if not re.search(r"20[0-9]{2}-[01][0-9]-[0-3][0-9]", t) or not re.search(r"fuente", t, re.I):
            duros.append(f"{c['id']}: un capítulo cerrado necesita al menos una fecha AAAA-MM-DD y una fuente citada")
        if c["id"] == "BP98" and re.search(r"⚠|\(interno\)|borrador", t, re.I):
            duros.append("BP98 (dossier) contiene ⚠ o notas internas: debe ser una versión para el cliente")
    for base in ("docs", "registro"):
        for p in sorted((repo / base).rglob("*")) if (repo / base).exists() else []:
            if p.suffix not in (".md", ".jsonl", ".sql", ".json") or "wiki" in p.parts:
                continue
            txt = re.sub(r"\]\([^)]*\)|https?://\S+", "", p.read_text(encoding="utf-8", errors="ignore"))
            for rx, que in PII:
                if rx.search(txt):
                    duros.append(f"{p.relative_to(repo)}: {que}")
    for ext in (".m", ".R", ".r"):
        for p in sorted((repo / "analisis").rglob(f"*{ext}")) if (repo / "analisis").exists() else []:
            t = p.read_text(encoding="utf-8")
            if not re.search(r"(?:fileread|fromJSON|read_json|jsondecode)\s*\(.*supuestos\.json", t):
                avisos.append(f"{p.relative_to(repo)}: no carga supuestos.json con una lectura real")
            for ln in t.splitlines():
                code = sin_cifras(ln)
                if re.search(r"(?<![\w.\[(])(?:[0-9]{2,}|[0-9]+\.[0-9]+)(?![\w\])])", code):
                    duros.append(f"{p.relative_to(repo)}: cifra tecleada en «{ln.strip()[:60]}»")
    return duros, avisos


if __name__ == "__main__":
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    d, a = auditar(repo)
    for x in a:
        print("  aviso:", x)
    for x in d:
        print("  ✗", x)
    print(f"{'✗' if d else '✓'} wiki corporativa: {len(d)} fallo(s) duro(s), {len(a)} aviso(s)")
    sys.exit(1 if d else 0)
