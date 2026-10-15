#!/usr/bin/env python3
"""
generar_areas.py — escribe las páginas de Área de wiki/AREAS/.

Una página de Área NO es un índice escrito a mano: su listado lo resuelve
Dataview contra el campo `area:` de cada nota, así que no puede
desincronizarse. Lo que sí es humano —y es la razón de que la página exista—
es la **definición**: qué entra en el Área y qué no.

Esa es la diferencia con las Áreas de Notion, que eran páginas sin contenido
propio y por eso no se replicaron en la migración del 2026-07-26.

Uso:
    python3 generar_areas.py <VAULT> [--forzar]

Sin `--forzar` no sobrescribe una página existente por debajo de la marca
`<!-- fin generado -->`, para no pisar lo que se haya escrito a mano.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

HOY = date.today().isoformat()
MARCA = "<!-- fin generado -->"

# (área, tags, definición, qué NO entra, temas conocidos, estado)
AREAS: list[tuple[str, str, str, str, list[str], str]] = [
    ("Investigación", "investigacion, ciencia",
     "El programa científico: la teoría TGDE y los cuatro sistemas donde se "
     "pone a prueba. Es el Área con densidad real de evidencia — cada cifra "
     "debe rastrearse a un notebook.",
     "Aplicaciones comerciales de un resultado (van a **Empresa**) e "
     "infraestructura para producirlo (va a **Sistema**).",
     ["Teoría TGDE", "Principia", "Motor ELEMENT", "Shewanella LC6",
      "HAMCAO", "Fucosa Sulfatada", "Vinaza", "Bitácora", "E. coli K-12",
      "Evidencia"],
     "Sobrerrepresentada: 74 de 99 notas. Es la fortaleza del vault y también "
     "su sesgo."),

    ("Empresa", "empresa, negocio",
     "Las tres líneas de negocio —Sapyria, AgroGlim, Biomined— más CIMMA y el "
     "método de lanzamiento. Comparten fundador y método, **no mercado**.",
     "La ciencia que las sostiene (va a **Investigación**) y los contactos "
     "concretos (van a **Relaciones** o **Clientes**).",
     ["Sapyria", "AgroGlim", "Biomined", "CIMMA", "Método 404", "Leyes",
      "Mercado"],
     "Cubierta. ⚠️ Graphify midió que esta capa cuelga de solo dos puentes "
     "científicos, [[HAMCAO]] y [[ELEMENT]]."),

    ("Sistema", "sistema, infraestructura",
     "El vault sobre sí mismo: su protocolo, sus auditorías, las skills, los "
     "agentes que lo consumen y el mapa de repos. Es la capa que hace que el "
     "resto sea recuperable.",
     "Conocimiento de dominio. Si una nota enseña biología o negocio, no es "
     "de esta Área aunque el vault la use.",
     ["Vault", "Amadeus", "Skills", "Proyectos", "Datos", "Hardware",
      "Notion", "Evidencia"],
     "Cubierta y medida por `vault-ops`."),

    ("Conocimiento", "conocimiento, biblioteca",
     "La biblioteca: lo que se lee para aprender, no lo que se produce. "
     "Corpus bibliográfico, apuntes de libros y material de referencia.",
     "Resultados propios (van a **Investigación**). Un paper que sostiene un "
     "resultado es `fuente:` de esa nota, no una nota de esta Área.",
     ["Referencias", "Apuntes libro", "Biografías", "Filosofía General",
      "Estoicismo", "Mentalidad", "Técnicas de estudio", "Patentes", "Leyes"],
     "🕳️ **Casi vacía: 1 nota.** En Notion era un Área con 24 Temas, todos "
     "con `0 Notes`. El marco existía; el contenido nunca se escribió."),

    ("Relaciones", "relaciones, personas",
     "Personas y organizaciones: quién es quién, cómo se llegó a ellos y qué "
     "se les debe. Una ficha por persona o entidad.",
     "Clientes con relación comercial activa (van a **Clientes**).",
     ["CRM", "Sector Agro", "Sector Minero", "Relaciones sociales",
      "Comunicación general", "Carisma y Magnetismo", "Linkedin",
      "Marca Personal"],
     "Una nota: [[Marca Personal y Presencia en LinkedIn]] (2026-08-31, "
     "primer contenido real del Tema `Marca Personal`). La base `People` de "
     "Notion sigue sin servir de CRM (44 invitados, campo `About` vacío) — "
     "esta nota no la resucita, es un punto de partida distinto."),

    ("Clientes", "clientes, comercial",
     "Quien paga o puede pagar: cuentas, propuestas enviadas, condiciones "
     "pactadas y estado de cada conversación comercial.",
     "Análisis de mercado agregado (va a **Empresa**, tema `Mercado`).",
     ["Propuestas", "Cuentas", "Pipeline"],
     "🕳️ **Vacía.** Material relacionado sin digerir en la bandeja: "
     "`Pitch BIomined_Nodo`, `Propuesta_Souther mininig picking`, "
     "`Propuesta para Southen mine`, `Prototipo 1- USIL`."),

    ("Finanzas", "finanzas, dinero",
     "Dinero personal y de las empresas: ingresos, costes, impuestos y "
     "proyecciones. Toda cifra con fecha y origen.",
     "Modelos tecno-económicos de una tecnología (van a **Empresa** junto a "
     "su línea de negocio).",
     ["Finanzas Personales", "Taxes", "Ventas", "Escalar un negocio",
      "Sapyria"],
     "Casi vacía: 1 nota, y es de economía unitaria de Sapyria, no personal."),

    ("Salud", "salud, personal",
     "Estado físico, entrenamiento, hábitos y seguimiento médico.",
     "Biología como disciplina (va a **Investigación** o **Conocimiento**).",
     ["Salud y Ejercicio", "Habitos", "Calestenia", "Gestión de tiempo",
      "Productividad"],
     "🕳️ **Vacía.** En Notion existían los Temas `Salud y Ejercicio` y "
     "`Calestenia_01`, ambos sin notas."),

    ("Talleres", "talleres, formacion",
     "Formación en cola y en curso: cursos, certificaciones y habilidades por "
     "adquirir, con su estado real —no la intención.",
     "Lo ya aprendido y sintetizado (va a **Conocimiento**).",
     ["Formación", "Aprender", "Automatizaciones", "Youtube",
      "Persuasión y manipulación", "Gestión de equipos", "Ventas"],
     "Dos notas: [[Escalera de Habilidades]] (A0–A14, ⚠️ declaración de "
     "intenciones de 2025, no registro de progreso) y "
     "[[Certificaciones y Formación Externa]] (2026-08-31, "
     "6 certificaciones externas reales verificadas — la primera medición "
     "de progreso real que tiene esta Área)."),
]


def pagina(area: str, tags: str, definicion: str, excluye: str,
           temas: list[str], estado: str) -> str:
    lista_temas = " · ".join(f"`{t}`" for t in temas)
    return f"""---
tags: [area, {tags}]
area: [{area}]
tema: [Áreas]
creado: {HOY}
actualizado: {HOY}
fuente: esquema Área/Tema del Notion "KaiToKid Dashboard", reconstruido {HOY}
---

# Área — {area}

{definicion}

**No entra aquí:** {excluye}

**Estado:** {estado}

## Temas

{lista_temas}

El Tema es vocabulario, no carpeta: se escribe en el campo `tema:` de la nota.
Esta lista viene del Notion original y **no es cerrada** — un Tema nuevo se usa
y ya, pero conviene añadirlo aquí para que no se dupliquen variantes.

## Notas de esta Área

```dataview
TABLE WITHOUT ID
  file.link AS "Nota",
  join(tema, ", ") AS "Tema",
  actualizado AS "Actualizada"
FROM "wiki"
WHERE contains(area, "{area}") AND file.name != this.file.name
SORT actualizado DESC
```

## Reparto por Tema

```dataview
TABLE WITHOUT ID
  rows.file.link AS "Notas",
  length(rows) AS "N"
FROM "wiki"
WHERE contains(area, "{area}") AND file.name != this.file.name
FLATTEN tema AS t
GROUP BY t
SORT length(rows) DESC
```

## Relacionado

- [[Mapa de Áreas]] — el índice de las nueve Áreas y su ocupación.

{MARCA}
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("vault", type=Path)
    ap.add_argument("--forzar", action="store_true")
    a = ap.parse_args()

    destino = a.vault / "wiki" / "AREAS"
    destino.mkdir(parents=True, exist_ok=True)

    for area, tags, d, ex, temas, estado in AREAS:
        f = destino / f"Área — {area}.md"
        if f.exists() and not a.forzar:
            print(f"· existe, se respeta: {f.name}")
            continue
        f.write_text(pagina(area, tags, d, ex, temas, estado), encoding="utf-8")
        print(f"✓ {f.name}")
    print(f"\n{len(AREAS)} Áreas en wiki/AREAS/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
