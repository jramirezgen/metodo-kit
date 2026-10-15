#!/usr/bin/env python3
"""Lo vendorizado es idéntico, o no está vendorizado: es una copia que divergió.

⛔ **El defecto que esto cierra, medido el 2026-09-08.** La skill lleva tres
ficheros que se copian a cada repo consumidor. Dos aguantaron —`canvas_lib.py` y
`base_lib.py` tienen el mismo md5 en los dos sitios— pero el tercero se rompió
sin que nadie se enterara:

| fichero | skill | `element/docs/wiki/` |
|---|---|---|
| `canvas_lib.py` | `c461af198a26…` | `c461af198a26…` |
| `base_lib.py`   | `e1fcc24125a9…` | `e1fcc24125a9…` |
| `publicar.py`   | **114 líneas**  | **277 líneas** |

El de `element` aprendió numeración densa, `.base`, fichas e índices de
colección; el de la skill seguía hablando de `docs/canvas/` y no conocía
`wiki.json`. **Nada lo comprobaba**, así que el siguiente proyecto que estrenara
la skill habría empezado con el publicador de hace tres versiones.

La causa raíz no era el descuido: era que `publicar.py` tenía **datos del
proyecto escritos dentro** (`tema: [Motor ELEMENT]`, `"00 — Ecuaciones de
ELEMENT"`). Un fichero con el nombre de un proyecto dentro no se puede
vendorizar, así que se copiaba y se editaba — que es exactamente cómo nace una
divergencia. Esos datos se fueron a `wiki.json`, y por eso este test puede
existir.

**La regla que fija:** se vendoriza lo que no tiene política. Lo específico del
proyecto vive en su manifiesto, nunca en el código copiado.

Uso: python3 scripts/tests/test_vendorizado.py
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

#: Los proyectos que este disco ya conoce. La lista no pretende ser universal:
#: es la que impide que vuelva a pasar lo que ya pasó.
PROYECTOS = ("ELEMENT", "APOLO")
NOMBRA_UN_PROYECTO = re.compile(
    r"(?:\bde |\bMotor )(?:%s)\b" % "|".join(PROYECTOS))

AQUI = Path(__file__).resolve().parent
SKILL = AQUI.parent.parent

#: Lo que se copia byte a byte a cada repo consumidor. Un generador entra aquí
#: cuando no sabe de qué proyecto es: `generar_ecuaciones.py` se queda fuera a
#: propósito —tabula las ecuaciones de un motor concreto— y `generar_lazo.py`
#: también. Los tres que sí entran (`incidencias`, `versiones`, y el `archivar`
#: que los alimenta) describen el wiki repo, no su contenido.
VENDORIZADOS = ("canvas_lib.py", "base_lib.py", "wiki_repo_lib.py",
                "publicar.py", "archivar.py", "generar_incidencias.py",
                "generar_versiones.py", "plan_canvas_lib.py")

#: Dónde aterrizan. Un consumidor ausente NO es un aprobado: se dice y se cuenta
#: aparte, porque «no lo pude comprobar» y «está bien» no son lo mismo.
CONSUMIDORES = (
    Path("/home/kaitokid/Documents/REPOSITORIOS/element/docs/wiki"),
    # La propia skill es consumidora: su `docs/wiki/` publica el mapa del
    # sistema con las mismas siete piezas. Omitirla sería la única copia que
    # nadie compara, y precisamente en el sitio del que salen todas.
    SKILL / "docs" / "wiki",
)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def main() -> int:
    print("vendorizado — la copia es idéntica o no es una copia")
    fallos = ausentes = 0

    for nombre in VENDORIZADOS:
        origen = SKILL / "scripts" / nombre
        if not origen.is_file():
            print(f"  ✗ la skill no trae {nombre}")
            fallos += 1
            continue
        h = sha(origen)
        for repo in CONSUMIDORES:
            destino = repo / nombre
            if not repo.is_dir():
                print(f"  ⚠ consumidor no montado: {repo}")
                ausentes += 1
                continue
            if not destino.is_file():
                print(f"  ✗ {repo.name}/{nombre}: no está vendorizado")
                fallos += 1
                continue
            hd = sha(destino)
            if hd == h:
                print(f"  ✓ {nombre} ≡ {repo.parent.parent.name}  ({h})")
            else:
                print(f"  ✗ {nombre} divergió: skill {h} · "
                      f"{repo.parent.parent.name} {hd}")
                fallos += 1

    # Lo específico del proyecto no puede estar dentro de lo vendorizado, o la
    # copia vuelve a ser inevitable. Se comprueba sobre el texto real.
    print("\nvendorizado — ningún fichero copiado nombra a un proyecto")
    for nombre in VENDORIZADOS:
        origen = SKILL / "scripts" / nombre
        if not origen.is_file():
            continue
        texto = origen.read_text(encoding="utf-8")
        codigo = "\n".join(l for l in texto.splitlines()
                           if not l.lstrip().startswith("#"))
        # El docstring del módulo cita ejemplos reales a propósito; lo que no
        # puede haber es un proyecto dentro del CÓDIGO.
        cuerpo = codigo.split('"""', 2)[-1] if '"""' in codigo else codigo
        # No se busca la palabra «ELEMENT» sino su FORMA de dato: «de <X>» es
        # como se nombra un artefacto de un proyecto («00 — Mapas de APOLO»),
        # y `tema: [Motor X]` es frontmatter de bóveda. Un `wiki/ELEMENT/` en
        # una docstring es un ejemplo, y los ejemplos sí pueden nombrar cosas.
        culpables = sorted({m.group(0) for m in NOMBRA_UN_PROYECTO.finditer(cuerpo)})
        if culpables:
            print(f"  ✗ {nombre} lleva dentro {culpables}: eso va en wiki.json")
            fallos += 1
        else:
            print(f"  ✓ {nombre} no nombra ningún proyecto")

    if ausentes:
        print(f"\n⚠ {ausentes} consumidor(es) no montado(s): no comprobados")
    print(f"\n{'✗' if fallos else '✓'} {fallos} divergencia(s)")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
