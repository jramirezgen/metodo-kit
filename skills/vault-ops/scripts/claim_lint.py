#!/usr/bin/env python3
"""Linting epistémico del vault: hace cumplir las CIFRAS CANÓNICAS. Sin LLM.

`vault_audit.py` mide la forma. Esto ataca el otro lado —que el Vault se
contradiga a sí mismo— aplicando DRY a los números: una cifra portante se declara
**una vez** en un registro, y el linter comprueba que ninguna nota la contradiga.

Por qué así y no al revés: un barrido ciego que agrupe todos los `R²` del Vault
devuelve un pajar (16 notas, 19 valores, casi todos legítimos porque son
experimentos distintos). El registro invierte el problema: solo se vigilan las
cifras que alguien declaró portantes, y ahí sí una discrepancia es señal.

Es el fallo que ya se pagó varias veces aquí: el RT-qPCR "0.72–0.84" inflado
resucitando en documentos que escaparon a una purga.

Modos:
    python claim_lint.py <raiz>                 # comprueba el registro
    python claim_lint.py <raiz> --descubrir     # barrido amplio, para POBLAR el
                                                # registro; ruidoso a propósito

El registro vive en `wiki/SISTEMA/Cifras Canónicas.md`, en una tabla Markdown:

    | id | etiquetas | valor | tolerancia | nota |
    | rtqpcr-nivelc | RT-qPCR, Pearson RT-qPCR | 0.50 | 0.03 | por qué es esta |

- `etiquetas`: alternativas separadas por **`;`** (basta que case una). Dentro de
  una etiqueta, **`+` exige que TODOS los términos estén en la línea**:
  `Spearman+biorreactor` no casa con una línea que solo diga "biorreactor".
  Sin ese Y, una etiqueta suficientemente distintiva no existe: o es tan amplia
  que dispara con todo, o tan literal que nunca aparece en prosa.
- Separadas por **`;`** (no por comas: chocan con los decimales
  `0,90`). Se buscan como texto plano dentro de cada línea.
- `tolerancia`: absoluta. `0` exige coincidencia exacta.
- `excluir` (columna opcional, `;`): si alguno de estos términos aparece en la
  línea, se ignora. Vía de escape para cuando otra métrica comparte la línea
  (p. ej. un `F1` junto a un `RT-qPCR`). Es preferible declararlo aquí a seguir
  afinando la expresión regular indefinidamente.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

RUTA_REGISTRO = "wiki/SISTEMA/Cifras Canónicas.md"
MARCADORES = ("⛔", "🛑", "⚠️", "🆕", "✅")

RE_NUM = re.compile(r"-?\d{1,4}(?:[.,]\d+)?")
RE_CLAIM = re.compile(
    r"([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ²³·\-]{1,24}|R²|AUC)"
    r"\s*(?:=|:|≈|~)?\s*(-?\d{1,4}(?:[.,]\d+)?)")


def num(s: str) -> float | None:
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def notas(raiz: Path) -> list[Path]:
    base = raiz / "wiki"
    if not base.is_dir():
        sys.exit(f"ERROR: no existe {base}")
    return sorted(base.rglob("*.md"))


def sin_frontmatter(texto: str) -> str:
    return re.sub(r"\A---\r?\n.*?\r?\n---", "", texto, flags=re.DOTALL)


def es_registro_historico(texto: str) -> bool:
    """¿La nota se declara REGISTRO HISTÓRICO en su frontmatter?

    Una bitácora transcribe lo que se reportó EN SU MOMENTO, incluidas cifras
    que después se corrigieron. Prohibirle nombrar el número viejo sería
    reescribir la historia, y ahí vive justamente la trazabilidad de POR QUÉ
    una cifra cambió.

    Declararse histórica NO silencia nada: los hallazgos se siguen listando,
    solo que en una sección aparte que no bloquea. La compuerta conserva todos
    sus dientes para las notas de síntesis, que es donde una cifra inflada hace
    daño de verdad porque se cita aguas abajo.

    Es deliberadamente un acto EXPLÍCITO por nota (`registro_historico: true`),
    no una exención por carpeta: eximir un directorio entero se olvida, y
    cualquier nota nueva heredaría el permiso sin que nadie lo decida.
    """
    m = re.match(r"\A---\r?\n(.*?)\r?\n---", texto, flags=re.DOTALL)
    if not m:
        return False
    return re.search(r"^\s*registro_historico\s*:\s*true\s*$",
                     m.group(1), flags=re.MULTILINE | re.IGNORECASE) is not None


def leer_registro(raiz: Path) -> list[dict]:
    p = raiz / RUTA_REGISTRO
    if not p.is_file():
        sys.exit(f"ERROR: no existe el registro {RUTA_REGISTRO}.\n"
                 f"Créalo, o usa --descubrir para ver qué cifras hay y poblarlo.")
    filas = []
    for linea in p.read_text(encoding="utf-8").splitlines():
        if not linea.strip().startswith("|"):
            continue
        c = [x.strip() for x in linea.strip().strip("|").split("|")]
        if len(c) < 4 or c[0].lower() in ("id", "") or set(c[0]) <= {"-", ":"}:
            continue
        valor, tol = num(c[2]), num(c[3])
        if valor is None:
            continue
        filas.append({
            "id": c[0],
            "etiquetas": [e.strip() for e in c[1].split(";") if e.strip()],
            "valor": valor,
            "tolerancia": tol if tol is not None else 0.0,
            "excluir": [e.strip() for e in c[4].split(";") if e.strip()] if len(c) > 4 else [],
            "nota": c[5] if len(c) > 5 else "",
        })
    if not filas:
        sys.exit(f"ERROR: {RUTA_REGISTRO} no tiene ninguna fila válida.")
    return filas


def contexto_por_parrafo(lineas: list[str]) -> list[str]:
    """Para cada línea, el texto en minúsculas del párrafo entero que la contiene.

    Un párrafo es un bloque contiguo de líneas no vacías. Sirve solo para evaluar
    la columna `excluir`: la detección de cifras sigue siendo estrictamente por
    línea. Ver el comentario en `comprobar`.
    """
    ctx: list[str] = [""] * len(lineas)
    i = 0
    while i < len(lineas):
        if not lineas[i].strip():
            ctx[i] = ""
            i += 1
            continue
        j = i
        while j < len(lineas) and lineas[j].strip():
            j += 1
        bloque = " ".join(lineas[i:j]).lower()
        for k in range(i, j):
            ctx[k] = bloque
        i = j
    return ctx


def comprobar(raiz: Path, registro: list[dict]) -> list[dict]:
    """Por cada etiqueta vigilada, mira los números de su misma línea."""
    hallazgos = []
    for p in notas(raiz):
        if p.name == Path(RUTA_REGISTRO).name:
            continue  # el registro declara los valores; no se audita a sí mismo
        crudo_nota = p.read_text(encoding="utf-8", errors="replace")
        historica = es_registro_historico(crudo_nota)
        cuerpo = sin_frontmatter(crudo_nota)
        lineas = cuerpo.splitlines()
        # La DETECCIÓN sigue siendo por línea (deliberado: un número de otra línea
        # no afirma lo mismo). Pero la EXCLUSIÓN se evalúa sobre el párrafo, que es
        # la unidad real de la prosa: markdown envuelve a ~80 caracteres, así que el
        # matiz que desactiva el hallazgo («reconciliar», «purgada», «era del»)
        # casi nunca cae en la misma línea que la cifra.
        #
        # Falso positivo que lo motivó (2026-08-01): «…hay que reconciliar sus /
        # cifras de RT-qPCR/Halley (0.667–0.842) contra el canónico actual / (0.50)»
        # ocupa tres líneas. `reconciliar` estaba en la primera, la cifra en la
        # segunda y el canónico en la tercera: ninguna exclusión podía funcionar.
        parrafos = contexto_por_parrafo(lineas)
        for n_linea, linea in enumerate(lineas, 1):
            for cifra in registro:
                low = linea.lower()
                # Una etiqueta casa si TODOS sus términos unidos por `+` están.
                if not any(all(term.strip() in low for term in e.lower().split("+"))
                           for e in cifra["etiquetas"]):
                    continue
                if any(x.lower() in parrafos[n_linea - 1] for x in cifra["excluir"]):
                    continue
                crudos = RE_NUM.findall(linea)
                canon = cifra["valor"]
                decimal_canon = canon != int(canon)
                # Solo cuentan los números que PODRÍAN estar afirmando lo mismo.
                # Sin esto, una línea que menciona "RT-qPCR (n=4)" se leería como
                # si afirmara que la correlación vale 4.
                comparables = []
                for m in crudos:
                    v = num(m)
                    if v is None:
                        continue
                    if decimal_canon and ("." not in m and "," not in m):
                        continue          # canónica decimal ⇒ enteros no compiten
                    if not (0.2 * abs(canon) <= abs(v) <= 5 * abs(canon)):
                        continue          # otro orden de magnitud ⇒ otra cosa
                    comparables.append(v)
                if not comparables:
                    continue              # la línea nombra la etiqueta, no la cifra
                if any(abs(v - canon) <= cifra["tolerancia"] for v in comparables):
                    continue
                valores = comparables
                hallazgos.append({
                    "id": cifra["id"],
                    "esperado": cifra["valor"],
                    "tolerancia": cifra["tolerancia"],
                    "nota": p.stem,
                    "linea": n_linea,
                    "encontrados": valores,
                    "texto": linea.strip()[:180],
                    "historico": historica,
                })
    return hallazgos


def descubrir(raiz: Path, min_notas: int) -> list[dict]:
    grupos: dict[str, dict[str, set]] = defaultdict(lambda: defaultdict(set))
    ejemplos: dict[tuple[str, str], str] = {}
    for p in notas(raiz):
        cuerpo = sin_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        for linea in cuerpo.splitlines():
            for etiqueta, valor in RE_CLAIM.findall(linea):
                v = num(valor)
                if v is None or (v.is_integer() and 1900 < v < 2200):
                    continue
                k = etiqueta.lower().rstrip(".,;:")
                grupos[k][f"{v:g}"].add(p.stem)
                ejemplos.setdefault((k, f"{v:g}"), linea.strip()[:150])
    salida = []
    for etiqueta, valores in grupos.items():
        todas = set().union(*valores.values())
        if len(valores) < 2 or len(todas) < min_notas:
            continue
        salida.append({"etiqueta": etiqueta, "n_valores": len(valores),
                       "n_notas": len(todas),
                       "valores": {v: sorted(ns) for v, ns in sorted(valores.items())},
                       "ejemplos": {v: ejemplos[(etiqueta, v)] for v in valores}})
    salida.sort(key=lambda d: -d["n_notas"])
    return salida


def enfasis(raiz: Path) -> dict:
    """Los marcadores de este Vault son PORTANTES: el índice decide con ellos.
    Si todo los lleva, dejan de señalar. Esto lo hace visible."""
    out = {}
    for p in notas(raiz):
        cuerpo = sin_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        n = max(len(cuerpo), 1)
        marcas = sum(cuerpo.count(m) for m in MARCADORES)
        out[p.stem] = {"marcadores": marcas,
                       "por_1000": round(1000 * marcas / n, 2),
                       "negritas_por_1000": round(1000 * cuerpo.count("**") / 2 / n, 2)}
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("raiz", type=Path)
    ap.add_argument("--descubrir", action="store_true")
    ap.add_argument("--min-notas", type=int, default=3)
    ap.add_argument("--limite", type=int, default=20)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    raiz = args.raiz.resolve()

    if args.descubrir:
        res = descubrir(raiz, args.min_notas)
        print(f"# Descubrimiento — {len(res)} etiquetas con más de un valor\n")
        print("⚠️ Ruidoso a propósito: sirve para **poblar el registro**, no para")
        print("acusar. Casi todas estas divergencias son legítimas.\n")
        for d in res[:args.limite]:
            print(f"## `{d['etiqueta']}` — {d['n_valores']} valores / {d['n_notas']} notas")
            for v, ns in d["valores"].items():
                print(f"- **{v}** — {', '.join(ns[:4])}{' …' if len(ns) > 4 else ''}")
            print()
        if args.json:
            args.json.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        return

    registro = leer_registro(raiz)
    hallazgos = comprobar(raiz, registro)
    e = enfasis(raiz)
    media = round(sum(v["por_1000"] for v in e.values()) / max(len(e), 1), 2)

    # Un registro histórico cita cifras que YA se corrigieron: se listan para
    # que nadie las pierda de vista, pero no bloquean la certificación.
    bloqueantes = [h for h in hallazgos if not h.get("historico")]
    historicos = [h for h in hallazgos if h.get("historico")]

    def tabla(hs: list[dict]) -> None:
        print("| Cifra | Esperado | Encontrado | Nota | Línea |")
        print("| --- | --- | --- | --- | --- |")
        for h in hs:
            print(f"| `{h['id']}` | {h['esperado']} ±{h['tolerancia']} | "
                  f"{', '.join(f'{v:g}' for v in h['encontrados'][:5])} | "
                  f"{h['nota']} | {h['linea']} |")
        print()

    print(f"# Linting epistémico — {len(registro)} cifras canónicas vigiladas\n")
    if not bloqueantes:
        print("✅ **Ninguna nota vigente contradice el registro.**\n")
    else:
        print(f"🛑 **{len(bloqueantes)} líneas contradicen una cifra canónica.**\n")
        tabla(bloqueantes)
        for h in bloqueantes:
            print(f"- **{h['id']}** en *{h['nota']}*:{h['linea']}\n  > {h['texto']}")
        print()

    if historicos:
        print(f"## ⚠️ {len(historicos)} en registros históricos (no bloquean)\n")
        print("Notas con `registro_historico: true`: transcriben lo que se reportó")
        print("en su momento. Se listan para no perderlas de vista — si alguna NO")
        print("es historia sino una afirmación vigente, quita el flag de esa nota.\n")
        tabla(historicos)

    top = sorted(e.items(), key=lambda kv: -kv[1]["por_1000"])[:5]
    print(f"## Densidad de marcadores (⛔🛑⚠️🆕✅)\n")
    print(f"Media del Vault: **{media}** por 1 000 caracteres. Son marcadores")
    print("*portantes* —el índice decide con ellos—, así que diluirlos los inutiliza.\n")
    print("| Nota | Por 1 000 | Total |")
    print("| --- | --- | --- |")
    for n, v in top:
        print(f"| {n} | {v['por_1000']} | {v['marcadores']} |")

    if args.json:
        args.json.write_text(json.dumps(
            {"registro": registro, "hallazgos": hallazgos, "enfasis": e},
            ensure_ascii=False, indent=2), encoding="utf-8")

    sys.exit(1 if bloqueantes else 0)


if __name__ == "__main__":
    main()
