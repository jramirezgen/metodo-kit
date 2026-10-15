#!/usr/bin/env python3
"""Regla 6: cerrar una incidencia (`situacion: resuelta`) commitea sola.

⛔ **Lo que esto prueba, y por qué con un repo git real.** `publicar.py`
detecta la transición comparando la `situacion` de HOY contra la que
`wiki.lock.json` observó la ÚLTIMA vez, y si acaba de entrar en `resuelta`
llama a `git add` + `git commit` de verdad sobre el repo de código. Mockear
`subprocess` habría probado que se llama a una función — no que el commit
existe, que el mensaje referencia la incidencia, ni que un segundo publish sin
cambios no lo duplica. Eso sólo lo demuestra `git log` sobre un repo real.

Uso: python3 scripts/tests/test_publicar_commit_incidencia.py
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import publicar as P  # noqa: E402


def ok(titulo: str, condicion: bool, detalle: str = "") -> bool:
    print(f"  {'✓' if condicion else '✗'} {titulo}"
          + (f" → {detalle}" if detalle and not condicion else ""))
    return condicion


# --------------------------------------------------------------------------
# Construcción de mensajes — puro, sin E/S
# --------------------------------------------------------------------------

def caso_mensaje_de_cierre() -> list[bool]:
    print("mensaje de cierre — el formato que pide el commit")
    ruta = Path("INC-009 — Un titulo bastante corto.md")
    cerrada_con_mapa = [("INC-009", {"ruta": ruta, "fm": {"mapa_n": 2}})]
    cerrada_sin_mapa = [("INC-011", {"ruta": Path("INC-011 — Otra cosa.md"),
                                     "fm": {}})]
    return [
        ok("con mapa_n: «mapa N» antes de «base de incidencias»",
           P._mensaje_de_cierre(cerrada_con_mapa, True) ==
           "wiki: cierra INC-009 (Un titulo bastante corto) — "
           "regenera mapa 2 y base de incidencias"),
        ok("sin mapa_n: sólo la base",
           P._mensaje_de_cierre(cerrada_sin_mapa, True) ==
           "wiki: cierra INC-011 (Otra cosa) — regenera base de incidencias"),
        ok("sin base declarada ni mapa: nombra el tablero igual",
           P._mensaje_de_cierre(cerrada_sin_mapa, False) ==
           "wiki: cierra INC-011 (Otra cosa) — regenera el tablero de incidencias"),
        ok("título largo se recorta con elipsis",
           len(P._titulo_corto(Path("INC-001 — " + "x" * 100 + ".md"))) == 60),
    ]


def caso_deteccion_de_transicion() -> list[bool]:
    print("\ndetección — sólo cuenta ENTRAR a resuelta, no quedarse ahí")
    actuales = {"INC-009": {"situacion": "resuelta", "ruta": Path("x"), "fm": {}},
               "INC-010": {"situacion": "en_curso", "ruta": Path("y"), "fm": {}}}
    return [
        ok("nueva, ya resuelta (sin `anterior`) cuenta como cierre",
           [i for i, _ in P._recien_cerradas(actuales, {})] == ["INC-009"]),
        ok("ya estaba resuelta la vez pasada: no vuelve a contar",
           P._recien_cerradas(actuales, {"INC-009": "resuelta"}) == []),
        ok("en curso no cuenta",
           "INC-010" not in dict(P._recien_cerradas(actuales, {}))),
        ok("sólo una transición real en esta muestra",
           len(P._recien_cerradas(actuales, {})) == 1),
    ]


# --------------------------------------------------------------------------
# Integración: un repo git real, una incidencia real
# --------------------------------------------------------------------------

def _sh(*args, cwd) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True,
                          check=True)


def _preparar_repo(tmp: Path) -> tuple[Path, Path, Path]:
    """`(repo, origen, carpeta_incidencias)`. `origen` es `repo/docs/wiki`."""
    repo = tmp / "repo"
    vault = tmp / "vault"
    origen = repo / "docs" / "wiki"
    origen.mkdir(parents=True)
    (vault / ".obsidian").mkdir(parents=True)

    _sh("git", "init", "-q", cwd=repo)
    _sh("git", "config", "user.email", "test@example.com", cwd=repo)
    _sh("git", "config", "user.name", "Test", cwd=repo)

    proyecto = "TESTP"
    carpeta = vault / "wiki" / proyecto / "Incidencias"
    carpeta.mkdir(parents=True)
    puerta = vault / "wiki" / proyecto / f"{proyecto}.md"
    puerta.write_text(
        "# TESTP\n\n- [[00 — Incidencias de TESTP|🐛 incidencias]]\n",
        encoding="utf-8")

    manifiesto = f"""{{
  "proyecto": "{proyecto}",
  "vault": "{vault.as_posix()}",
  "git_commit_al_cerrar_incidencia": true,
  "coautoria_commit": "Coautor De Prueba <prueba@example.com>",
  "estructura": {{"mapas": "Mapas", "bases": "Bases",
                  "incidencias": "Incidencias"}},
  "frontmatter": {{"area": ["Sistema"], "tema": ["Test"]}},
  "mapas": [],
  "bases": [
    {{
      "n": 1,
      "titulo": "Incidencias de {proyecto}",
      "fuente": "01 — Incidencias de {proyecto}.base",
      "generador": "docs/wiki/generar_incidencias.py",
      "tabula": "el tablero",
      "indice": "00 — Incidencias de {proyecto}",
      "gancho": "🐛 incidencias"
    }}
  ]
}}
"""
    (origen / "wiki.json").write_text(manifiesto, encoding="utf-8")
    _escribir_incidencia(carpeta, "en_curso", hito="")
    _sh("git", "add", "-A", cwd=repo)
    _sh("git", "commit", "-q", "-m", "chore: estreno del wiki repo de prueba",
       cwd=repo)
    return repo, origen, carpeta


def _escribir_incidencia(carpeta: Path, situacion: str, hito: str = "v1") -> Path:
    ruta = carpeta / "INC-009 — Un cierre para probar.md"
    ruta.write_text(f"""---
tags: [incidencia, testp]
area: [Sistema]
tema: [Test]
inc: INC-009
situacion: {situacion}
tipo: defecto
peso: 3
hito: "{hito if situacion == 'resuelta' else ''}"
bloqueado_por: []
mapa_n:
nodo:
---

# Un cierre para probar

## Qué pasa

Nada real: es la incidencia del test.

## Cómo se sabe que está mal

Este mismo test.

## Qué la cierra

Que `situacion` pase a `resuelta`.
""", encoding="utf-8")
    return ruta


def _log(repo: Path) -> list[str]:
    r = _sh("git", "log", "--format=%s", cwd=repo)
    return r.stdout.splitlines()


def caso_commit_automatico_al_cerrar() -> list[bool]:
    print("\nintegración — cerrar de verdad commitea de verdad")
    R = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        repo, origen, carpeta = _preparar_repo(tmp)
        antes = _log(repo)

        # Publicar sin que nada haya cambiado de situación: no debe commitear.
        codigo = P.publicar(origen)
        R.append(ok("primera corrida sin cambios: éxito", codigo == 0))
        R.append(ok("y sin commit nuevo (no hay transición que cerrar)",
                    _log(repo) == antes, f"{_log(repo)} vs {antes}"))

        # Alguien dejó otra cosa preparada en el índice para su propio commit.
        (repo / "ajeno.txt").write_text("no es del cierre\n", encoding="utf-8")
        _sh("git", "add", "ajeno.txt", cwd=repo)

        # Se cierra la incidencia, tal como lo haría una persona en Obsidian.
        _escribir_incidencia(carpeta, "resuelta")
        codigo = P.publicar(origen)
        despues = _log(repo)
        R.append(ok("segunda corrida (con cierre): éxito", codigo == 0))
        R.append(ok("nace exactamente un commit nuevo",
                    len(despues) == len(antes) + 1,
                    f"{despues} vs {antes}"))
        if len(despues) > len(antes):
            mensaje = despues[0]
            R.append(ok("el commit referencia INC-009",
                        mensaje.startswith("wiki: cierra INC-009"), mensaje))
            R.append(ok("y su título corto",
                        "Un cierre para probar" in mensaje, mensaje))
            R.append(ok("y dice qué regenera",
                        "base de incidencias" in mensaje, mensaje))
            cuerpo = _sh("git", "log", "-1", "--format=%B", cwd=repo).stdout
            R.append(ok("firma con la coautoría que declara el manifiesto",
                        "Co-Authored-By: Coautor De Prueba <prueba@example.com>"
                        in cuerpo, cuerpo))
            R.append(ok("y con ninguna otra escrita en el código",
                        cuerpo.count("Co-Authored-By:") == 1, cuerpo))
            tocados = _sh("git", "show", "--name-only", "--format=",
                          "HEAD", cwd=repo).stdout
            R.append(ok("el commit lleva wiki.lock.json",
                        "wiki.lock.json" in tocados, tocados))
            R.append(ok("y la base del tablero",
                        "Incidencias de TESTP.base" in tocados, tocados))
            R.append(ok("pero NO lo que otro dejó preparado en el índice",
                        "ajeno.txt" not in tocados, tocados))
            preparado = _sh("git", "diff", "--cached", "--name-only",
                            cwd=repo).stdout
            R.append(ok("que sigue preparado, esperando su propio commit",
                        "ajeno.txt" in preparado, preparado))

        # Publicar otra vez sin tocar nada: no se duplica el commit del cierre.
        codigo = P.publicar(origen)
        R.append(ok("tercera corrida (ya resuelta, sin cambio): éxito",
                    codigo == 0))
        R.append(ok("no nace un segundo commit de cierre",
                    _log(repo) == despues, f"{_log(repo)} vs {despues}"))
    return R


def caso_capacidad_desactivada_no_commitea() -> list[bool]:
    print("\nintegración — con la capacidad en `false`, publicar no toca git")
    R = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        repo, origen, carpeta = _preparar_repo(tmp)
        manifiesto = (origen / "wiki.json").read_text(encoding="utf-8")
        manifiesto = manifiesto.replace(
            '"git_commit_al_cerrar_incidencia": true',
            '"git_commit_al_cerrar_incidencia": false')
        (origen / "wiki.json").write_text(manifiesto, encoding="utf-8")
        _sh("git", "add", "-A", cwd=repo)
        _sh("git", "commit", "-q", "-m", "chore: desactiva la capacidad",
           cwd=repo)
        antes = _log(repo)

        _escribir_incidencia(carpeta, "resuelta")
        codigo = P.publicar(origen)
        R.append(ok("publica igual de bien", codigo == 0))
        R.append(ok("pero no commitea nada por su cuenta",
                    _log(repo) == antes, f"{_log(repo)} vs {antes}"))
    return R


def caso_primera_activacion_no_firma_cierres_viejos() -> list[bool]:
    print("\nintegración — activar la capacidad sobre un tablero con resueltas")
    R = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        repo, origen, carpeta = _preparar_repo(tmp)
        # La incidencia ya estaba cerrada ANTES de que nadie activara la Regla 6.
        _escribir_incidencia(carpeta, "resuelta")
        antes = _log(repo)
        codigo = P.publicar(origen)
        R.append(ok("la primera publicación funciona", codigo == 0))
        R.append(ok("y no firma como recién cerrada una resuelta de antes",
                    _log(repo) == antes, f"{_log(repo)} vs {antes}"))
        lock = P._leer_json_lock(origen)
        R.append(ok("pero deja la línea base en el lock",
                    lock.get(P.CLAVE_INCIDENCIAS, {}).get("INC-009") == "resuelta",
                    str(lock.get(P.CLAVE_INCIDENCIAS))))
        codigo = P.publicar(origen)
        R.append(ok("y la siguiente tampoco inventa un cierre",
                    codigo == 0 and _log(repo) == antes, f"{_log(repo)} vs {antes}"))
    return R


def caso_tablero_rechazado_no_commitea() -> list[bool]:
    print("\nintegración — si el tablero rechaza el cierre, no hay commit (ATALANTA INC-067)")
    R = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        repo, origen, carpeta = _preparar_repo(tmp)
        R.append(ok("línea base publicada", P.publicar(origen) == 0))
        antes = _log(repo)
        # `resuelta` sin `hito`: el generador del tablero la rechaza y aborta.
        _escribir_incidencia(carpeta, "resuelta", hito="")
        codigo = P.publicar(origen)
        R.append(ok("la publicación falla", codigo != 0, str(codigo)))
        R.append(ok("y NO nace commit de cierre", _log(repo) == antes,
                    f"{_log(repo)} vs {antes}"))
        lock = P._leer_json_lock(origen)
        R.append(ok("el lock conserva la situación anterior (en_curso)",
                    lock.get(P.CLAVE_INCIDENCIAS, {}).get("INC-009") == "en_curso",
                    str(lock.get(P.CLAVE_INCIDENCIAS))))
        # Se arregla el hito y se republica: ahora sí, exactamente un commit.
        _escribir_incidencia(carpeta, "resuelta", hito="v1")
        codigo = P.publicar(origen)
        R.append(ok("arreglado, publica", codigo == 0, str(codigo)))
        R.append(ok("y nace exactamente el commit del cierre",
                    len(_log(repo)) == len(antes) + 1
                    and _log(repo)[0].startswith("wiki: cierra INC-009"), str(_log(repo))))
    return R


def main() -> int:
    r = (caso_mensaje_de_cierre() + caso_deteccion_de_transicion()
        + caso_commit_automatico_al_cerrar()
        + caso_capacidad_desactivada_no_commitea()
        + caso_primera_activacion_no_firma_cierres_viejos()
        + caso_tablero_rechazado_no_commitea())
    print(f"\n{sum(r)}/{len(r)} verde")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
