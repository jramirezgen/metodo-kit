# Reglas de arquitectura y diseño (extraídas de F:\skills\Programacion y matematicas)

Estas skills se generaron a partir de paquetes de
`/mnt/f/skills/Programacion y matematicas/` (`F:\skills\Programacion y
matematicas\` en Windows). No son copias — son síntesis de los principios
clave de cada una, reformulados como reglas de arquitectura/diseño para este
workspace (`~/Documents/REPOSITORIOS`). Las primeras 8 (2026-09-05) cubren
principios de código; `autonomous-loop` (2026-09-06) es distinta de
naturaleza — es disciplina de proceso para trabajo largo, no un principio de
diseño — y se orquesta desde el router `code-principles` igual que las otras.

## Mapeo origen → skill local

| Origen (F:\skills) | Skill local |
|---|---|
| `Domain-drive-design/` | [`domain-driven-design/`](domain-driven-design/SKILL.md) |
| `Functional-programmer-inmutabilty/` | [`functional-immutability/`](functional-immutability/SKILL.md) |
| `Test-Driven-Development/` | [`test-driven-development/`](test-driven-development/SKILL.md) |
| `clean-architecture-1.0.0/` + `principle-clean-architecture-1.0.0/` | [`clean-architecture/`](clean-architecture/SKILL.md) (las dos se fusionaron: cubrían el mismo tema) |
| `code-refactoring-refactor-clean-1.0.0/` | [`refactoring-clean-code/`](refactoring-clean-code/SKILL.md) |
| `defense-in-depth-1.0.0/` | [`defense-in-depth/`](defense-in-depth/SKILL.md) |
| `pragmatic-programmer-1.0.0/` | [`pragmatic-programmer-base/`](pragmatic-programmer-base/SKILL.md) — **renombrada** (ver nota abajo) |
| `separation-of-concerns-pattern-overview-1.0.0/` | [`separation-of-concerns/`](separation-of-concerns/SKILL.md) |
| `autonomous-loop-1.0.0/` | [`autonomous-loop/`](autonomous-loop/SKILL.md) — solo la disciplina (fases + estado + re-anclaje); el Stop hook y los comandos `/auto-loop` del paquete original **no se instalaron** porque dependen de plugins (`/workflows:*`, `/compound-engineering:*`) ausentes aquí |

## Por qué `pragmatic-programmer-base` y no `pragmatic-programmer`

Este entorno ya tenía una skill **global** llamada `pragmatic-programmer`
(propósito: "LEER PRIMERO antes de escribir o modificar código", con una
adaptación al dominio ELEMENT/TGDE). Nombrar igual a la skill local habría
generado ambigüedad de nombre (`pragmatic-programmer` vs. la variante scoped a
este directorio). Se optó por `pragmatic-programmer-base` para la versión
genérica extraída de la librería `F:\skills`, dejando la global intacta.

## Cómo se cargan

Cada carpeta es un `SKILL.md` con frontmatter `name` + `description`. Claude
Code las detecta al iniciar sesión y las muestra en el listado de skills
disponibles — se invocan automáticamente cuando la tarea coincide con su
`description`, o explícitamente con `/nombre-de-la-skill`.

**Importante**: como se crearon a mitad de esta sesión, no van a aparecer en
el listado de skills disponibles hasta la **próxima sesión** de Claude Code en
este workspace (el escaneo de `.claude/skills/` ocurre al arrancar). En esta
misma sesión se pueden invocar leyendo el archivo directamente o con el tool
`Skill` si el harness ya las registró.

## Alcance

Cubren: arquitectura en capas (Clean/Hexagonal + SOLID), modelado de dominio
(DDD orientado a datos y a tipos), TDD, programación funcional/inmutabilidad,
refactor con umbrales objetivos, defensa en profundidad para validación de
datos, separación orquestación/negocio, y los meta-principios de "The
Pragmatic Programmer". No sustituyen la lectura de las skills originales para
casos borde — cada una referencia su origen en el frontmatter (`metadata.origen`).
