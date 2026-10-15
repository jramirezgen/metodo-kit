"""Paquetes de revisión externa por rol (abogado, contador…), derivados de UN documento de validación (VAL).

    python3 docs/validacion/generar_paquetes.py              # escribe docs/validacion/paquetes/<rol>/
    python3 docs/validacion/generar_paquetes.py --comprobar  # sale 1 si lo escrito no coincide con lo que se generaría

Configuración en `docs/validacion/paquetes.json`:
    {"val": "docs/validacion/VAL.md",
     "roles": {"abogado": {"clases": ["A","AC"], "resumen": "docs/validacion/resumen_abogado.md", "anexos": ["docs/…md"]},
               "contador": {"clases": ["C","AC"], "resumen": "…", "anexos": ["…"], "cifras": true}}}

Formato esperado del VAL: bloques `## X. …`; cada pregunta `### VAL-NN · …` con una línea `- **Clase:** A|C|AC` y, opcional, una línea
`- **Origen:** …` (rutas internas, que NO viajan). Stdlib pura, sin reloj ni azar: lo commiteado debe coincidir con lo generado."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CONF = json.loads((RAIZ / "docs" / "validacion" / "paquetes.json").read_text(encoding="utf-8"))
SALIDA = RAIZ / "docs" / "validacion" / "paquetes"
RUTA = re.compile(r"`([^`]*(?:/|\.py|\.csv|\.md|\.json)[^`]*)`")
IDENT = re.compile(r"`([a-z][a-z0-9_]*)`")


def limpiar(t: str) -> str:
    """Quita rutas y nombres de código: lo interno no se comparte con el profesional."""
    return IDENT.sub(lambda m: m.group(1).replace("_", " "), RUTA.sub("documento interno", t))


def preguntas(texto: str):
    out, bloque = [], ""
    for parte in re.split(r"(?m)^(?=#{2,3} )", texto):
        if parte.startswith("## "):
            bloque = parte.split("\n", 1)[0]
        m = re.match(r"### (VAL-\d+) · ", parte)
        if m:
            c = re.search(r"\*\*Clase:\*\* (AC|A|C)\b", parte)
            out.append((bloque, m.group(1), c.group(1) if c else "", parte))
    return out


def tabla_cifras(texto: str) -> str:
    m = re.search(r"<!-- GENERADO:val_cifras -->(.*?)<!-- /GENERADO:val_cifras -->", texto, re.S)
    filas = []
    for l in (m.group(1) if m else "").splitlines():
        if l.startswith("|"):
            filas.append("| " + " | ".join(c.strip() for c in l.strip().strip("|").split("|")[:-1]) + " |")  # sin columna Fuente
    return "\n".join(filas)


def paquete(rol: str, cfg: dict, val: str) -> str:
    elegidas = [q for q in preguntas(val) if q[2] in set(cfg["clases"])]
    p = [f"# Paquete de revisión · {rol}\n", (RAIZ / cfg["resumen"]).read_text(encoding="utf-8")]
    if cfg.get("cifras"):
        p.append("### Cifras de impacto\n\nSon de modelo, no contabilidad cerrada.\n\n" + tabla_cifras(val))
    p.append(f"## Preguntas para el {rol}\n\n{len(elegidas)} preguntas. Clase AC = las responden ambos.\n")
    ultimo = None
    for enc, _i, _c, texto in elegidas:
        if enc != ultimo:
            p.append(f"\n{enc}\n")
            ultimo = enc
        p.append(limpiar(re.sub(r"(?m)^- \*\*Origen:\*\*.*\n?", "", texto.rstrip())))
    p += [f"## Registro de respuestas\n\nAcepto, Ajusto o Rechazo, con norma y artículo si la hay. Firma por rol, sin nombres.\n",
          "| ID | Clase | Respuesta | Fecha | Firma |", "|---|---|---|---|---|"]
    p += [f"| {i} | {c} | ____ | ____ | ____ |" for _, i, c, _ in elegidas]
    p.append("\n## Anexos que acompañan este paquete\n\n" + "\n".join(f"- `anexos/{Path(a).name}`" for a in cfg["anexos"]))
    return "\n".join(x.rstrip("\n") + "\n" for x in p)


def generar() -> dict[Path, str]:
    val = (RAIZ / CONF["val"]).read_text(encoding="utf-8")
    out = {}
    for rol, cfg in CONF["roles"].items():
        out[SALIDA / rol / f"PAQUETE_{rol.upper()}.md"] = paquete(rol, cfg, val)
        for a in cfg["anexos"]:
            out[SALIDA / rol / "anexos" / Path(a).name] = (RAIZ / a).read_text(encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    salida = generar()
    if "--comprobar" in argv:
        malos = [str(p.relative_to(RAIZ)) for p, t in salida.items() if not p.is_file() or p.read_text(encoding="utf-8") != t]
        print("paquetes al día" if not malos else "desactualizados: " + ", ".join(malos))
        return 1 if malos else 0
    for p, t in salida.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(t, encoding="utf-8")
    print(f"{len(salida)} archivos en {SALIDA.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
