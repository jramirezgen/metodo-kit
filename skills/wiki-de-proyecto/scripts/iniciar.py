#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""El comando que convierte un repo en **wiki repo**, y el que lo pone al día.

Un *wiki repo* es un repo cuya documentación viva **no está en el repo**: está
en la carpeta del proyecto dentro de la bóveda de Obsidian, donde se lee y se
edita a mano, y el repo guarda **la intención** de esa carpeta —los generadores
y `wiki.json`— con las mismas garantías que git le da al código.

    repo                          bóveda
    ────                          ──────
    docs/wiki/*.py   generan →    wiki/<PROYECTO>/**            (árbol de trabajo)
    docs/wiki/wiki.json           ←── lo que debería haber      (índice)
    docs/wiki/wiki.lock.json      ←── lo que de verdad hay      (HEAD + huellas)

Este script hace **dos** cosas, y decide cuál por lo que encuentra, no por una
bandera —una bandera que hay que acordarse de poner es una bandera que un día
no se pone—:

  · **estrenar** (no hay `wiki.json`): crea `docs/wiki/`, copia las piezas,
    siembra el manifiesto y la plantilla de generador, prepara la carpeta de la
    bóveda y su nota puerta.
  · **poner al día** (ya hay `wiki.json`): **sólo** re-copia las piezas
    vendorizadas. No toca el manifiesto ni los generadores del proyecto. Es la
    respuesta a *«¿con qué comando vuelvo a poner esto al día?»*, y es segura de
    correr las veces que haga falta.

Sin `--aplicar` no escribe nada: dice qué haría. El destino de una operación que
no se puede ensayar se descubre después, y después ya está hecho.

Uso:
    python3 iniciar.py <repo> --proyecto APOLO --mapas-de APOLO   # ensayo
    python3 iniciar.py <repo> --proyecto APOLO --aplicar          # de verdad
    python3 iniciar.py <repo> --aplicar                           # poner al día
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import shutil
import sys
from datetime import date
from pathlib import Path

AQUI = Path(__file__).resolve().parent
HOY = date.today().isoformat()
VAULT_POR_DEFECTO = "/mnt/f/OBSIDIAN"

#: Las nueve Áreas del vault son vocabulario CERRADO (protocolo del vault, §
#: «El esquema Área/Tema»). Se ofrece la que casi siempre aplica y se avisa.
AREA_POR_DEFECTO = "Investigación"


def vendorizados() -> tuple[str, ...]:
    """La lista canónica vive en el test de vendorizado, y se lee de ahí.

    Declararla dos veces significa que un día habrá dos listas distintas, y la
    que decide no será la que alguien miró.
    """
    fuente = (AQUI / "tests" / "test_vendorizado.py").read_text(encoding="utf-8")
    for nodo in ast.walk(ast.parse(fuente)):
        if (isinstance(nodo, ast.Assign)
                and any(getattr(t, "id", None) == "VENDORIZADOS"
                        for t in nodo.targets)):
            return tuple(ast.literal_eval(nodo.value))
    raise SystemExit("✗ la skill ya no declara VENDORIZADOS: no sé qué copiar")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def copiar_piezas(destino: Path, *, aplicar: bool) -> int:
    """Deja las piezas de la skill en `docs/wiki/`. Idempotente por diseño."""
    cambios = 0
    for nombre in vendorizados():
        origen = AQUI / nombre
        if not origen.is_file():
            print(f"  ✗ la skill no trae `{nombre}`")
            continue
        fin = destino / nombre
        if fin.is_file() and _sha(fin) == _sha(origen):
            print(f"  · {nombre} ya está al día")
            continue
        estado = "actualiza" if fin.is_file() else "copia"
        print(f"  {'→' if aplicar else '~'} {estado} {nombre}")
        if aplicar:
            shutil.copy2(origen, fin)
        cambios += 1
    return cambios


def manifiesto_inicial(proyecto: str, vault: str, mapas_de: str,
                       area: str, tema: str) -> dict:
    """Lo que un wiki repo declara de sí mismo, y nada más.

    `mapas` y `bases` nacen **vacíos** a propósito: un manifiesto sembrado con
    un mapa de ejemplo publica un mapa de ejemplo en la bóveda de alguien.
    """
    # Cuando los mapas son del propio proyecto, `APOLO/Mapas` dentro de
    # `wiki/APOLO/` sería una carpeta que repite su propio nombre. El nivel
    # extra existe para separar los mapas de UNA pieza (APOLO) de los del repo
    # que la contiene (ELEMENT); si no hay dos, no hace falta.
    sub = f"{mapas_de}/Mapas" if mapas_de != proyecto else "Mapas"
    return {
        "_": (f"Manifiesto del wiki repo de {proyecto}. Lo que este fichero "
              f"declara es la INTENCIÓN; lo que la bóveda tiene de verdad está "
              f"en `wiki.lock.json`, que es generado y no se edita a mano."),
        "proyecto": proyecto,
        "vault": vault,
        "estructura": {
            "mapas": sub,
            "mapas_de": mapas_de,
            "versiones": f"{sub}/Versiones",
            "bases": "Bases",
            "incidencias": "Incidencias",
        },
        "frontmatter": {"area": [area], "tema": [tema]},
        "_mapas": ("Cada mapa: n · fuente (el .canvas del repo) · titulo · "
                   "mapea · generador · libres (ids que el humano puede mover). "
                   "Opcional `issue`."),
        "mapas": [],
        "_bases": ("Cada base: n · titulo · fuente (.base) · generador · "
                   "tabula · indice (la nota 00 que la abre) · gancho (cómo se "
                   "la nombra desde la nota puerta)."),
        "bases": [],
    }


def nota_puerta(proyecto: str, area: str, tema: str) -> str:
    """La única pieza que un humano tiene que mantener, y por eso se siembra.

    `publicar.py` se niega a publicar si esta nota no enlaza los índices: es la
    cadena `index.md → puerta → carpeta`, y sin ella lo publicado existe en el
    disco pero no existe para nadie.
    """
    return "\n".join([
        "---",
        "tags: [indice, proyecto]",
        f"area: [{area}]",
        f"tema: [{tema}]",
        f"creado: {HOY}",
        f"actualizado: {HOY}",
        f'resumen: "La puerta de {proyecto}: desde aquí se llega a sus mapas y '
        f'a sus bases."',
        "submapa: true",
        "---",
        "",
        f"# {proyecto}",
        "",
        "*(qué es este proyecto, en dos líneas — esto sí se escribe a mano)*",
        "",
        "## Los mapas y las bases",
        "",
        "> Los renglones de aquí abajo los pide `publicar.py` cuando publica "
        "algo que nadie enlaza: los dicta él, con el texto exacto, y se pegan.",
        "",
        "## Relacionado",
        "",
    ]) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", type=Path, help="raíz del repo que será wiki repo")
    ap.add_argument("--proyecto", help="NOMBRE de la carpeta en wiki/ del vault")
    ap.add_argument("--mapas-de", help="titular de los mapas (por defecto, el "
                                       "propio proyecto)")
    ap.add_argument("--vault", default=VAULT_POR_DEFECTO)
    ap.add_argument("--area", default=AREA_POR_DEFECTO,
                    help="una de las nueve Áreas del vault (vocabulario cerrado)")
    ap.add_argument("--tema", help="tema del frontmatter (por defecto, el proyecto)")
    ap.add_argument("--aplicar", action="store_true",
                    help="sin esto no escribe nada: sólo dice qué haría")
    a = ap.parse_args(argv)

    repo = a.repo.resolve()
    if not repo.is_dir():
        print(f"✗ no existe el repo: {repo}")
        return 2
    destino = repo / "docs" / "wiki"
    manifiesto = destino / "wiki.json"
    estrena = not manifiesto.is_file()

    print(f"{'estrenar' if estrena else 'poner al día'} — {repo}"
          f"{'' if a.aplicar else '   (ENSAYO: no se escribe nada)'}\n")

    if not estrena:
        # Poner al día NO toca el manifiesto ni los generadores del proyecto.
        # Un comando que puede pisar `wiki.json` es un comando que nadie corre
        # dos veces, y entonces las copias vuelven a divergir.
        print("ya es un wiki repo; se re-copian sólo las piezas de la skill")
        cambios = copiar_piezas(destino, aplicar=a.aplicar)
        print(f"\n{'✓' if a.aplicar else '~'} {cambios} pieza(s) "
              f"{'actualizada(s)' if a.aplicar else 'por actualizar'}")
        if cambios and not a.aplicar:
            print("  vuelve a correrlo con --aplicar")
        return 0

    if not a.proyecto:
        print("✗ para estrenar hace falta --proyecto: es el nombre de la "
              "carpeta que se creará en wiki/ de la bóveda")
        return 2
    proyecto = a.proyecto
    mapas_de = a.mapas_de or proyecto
    tema = a.tema or proyecto
    vault = Path(a.vault)
    if not vault.is_dir():
        print(f"✗ no existe la bóveda: {vault}")
        return 2

    raiz = vault / "wiki" / proyecto
    if raiz.exists() and any(raiz.iterdir()):
        print(f"⚠ `wiki/{proyecto}/` ya existe y tiene cosas dentro. No se "
              f"borra nada: lo que haya se conserva y `publicar.py` se negará "
              f"a pisar lo que no se haya adoptado.")

    print("en el repo")
    if a.aplicar:
        destino.mkdir(parents=True, exist_ok=True)
    print(f"  {'→' if a.aplicar else '~'} docs/wiki/")
    copiar_piezas(destino, aplicar=a.aplicar)
    print(f"  {'→' if a.aplicar else '~'} wiki.json  (proyecto {proyecto}, "
          f"mapas de {mapas_de})")
    if a.aplicar:
        manifiesto.write_text(
            json.dumps(manifiesto_inicial(proyecto, str(vault), mapas_de,
                                          a.area, tema),
                       ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        plantilla = AQUI / "plantilla_generador.py"
        if plantilla.is_file():
            shutil.copy2(plantilla, destino / "plantilla_generador.py")
    print(f"  {'→' if a.aplicar else '~'} plantilla_generador.py  "
          f"(cópiala a generar_<lo tuyo>.py y edítala)")

    print("\nen la bóveda")
    est = manifiesto_inicial(proyecto, str(vault), mapas_de, a.area, tema)
    for clave in ("mapas", "versiones", "bases", "incidencias"):
        sub = raiz / est["estructura"][clave]
        print(f"  {'→' if a.aplicar else '~'} wiki/{proyecto}/"
              f"{est['estructura'][clave]}/")
        if a.aplicar:
            sub.mkdir(parents=True, exist_ok=True)
    puerta = raiz / f"{proyecto}.md"
    if puerta.is_file():
        print(f"  · {proyecto}.md ya existe: no se toca")
    else:
        print(f"  {'→' if a.aplicar else '~'} {proyecto}.md  (la nota puerta; "
              f"sin ella `publicar.py` se niega a publicar)")
        if a.aplicar:
            puerta.write_text(nota_puerta(proyecto, a.area, tema),
                              encoding="utf-8")

    print(f"""
{'✓ estrenado' if a.aplicar else '~ esto es lo que haría; añade --aplicar'}

Lo que falta, y no lo puede hacer este script:

  1. Escribe tu generador: copia `plantilla_generador.py` a
     `docs/wiki/generar_<lo tuyo>.py` y declara el mapa en `wiki.json`
     (`mapas[]`: n · fuente · titulo · mapea · generador · libres).
  2. Genera el `.canvas` y publica en ensayo:
       python3 docs/wiki/generar_<lo tuyo>.py docs/wiki/<lo tuyo>.canvas
       python3 docs/wiki/publicar.py docs/wiki --simulacro
  3. Enlaza desde `{proyecto}.md` los índices que `publicar.py` te dicte —
     te da el renglón exacto— y publica de verdad:
       python3 docs/wiki/publicar.py docs/wiki
  4. Registra `{proyecto}.md` en el `index.md` de la bóveda (o en el sub-mapa
     que corresponda) **en la misma operación**, e indexa:
       python3 /mnt/f/skills/_personales/vault-ops/scripts/vault_audit.py {vault}

⚠ `--area {a.area}` sale del vocabulario CERRADO de nueve Áreas del vault.
   Si no es la tuya, vuelve a correrlo con la correcta antes de publicar.""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
