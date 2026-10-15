# Kit de método — cómo se hacen proyectos grandes con un agente, sin perder el hilo

Paquete portable con **todo lo usado** para llevar pipelines largos y exigentes (AQUERONTE, ATALANTA, AJOLOTE, QRECAUDA, SAPYRIA…) con rigor: skills, plantillas, convenciones de git, tablero de incidencias, DAG verificable, wiki repo, segundo cerebro y las reglas de trabajo con un agente LLM. Sirve para cualquier dominio (software, ciencia, empresa), no sólo para el que lo originó.

La idea central en una línea: **el estado vive en el disco (git + registro + wiki), nunca en el chat ni en la memoria del agente, y cada regla es un test o un hook que muerde, no prosa.**

## Qué hay dentro

| Carpeta / archivo | Qué es |
|---|---|
| `INSTALAR.sh`, `VERIFICAR.sh` | Instalación en un comando (reescribe rutas) y comprobación con un repo de prueba desechable |
| `USAGE.md` | **Empieza aquí.** Flujo completo de un proyecto, con los comandos en orden |
| `docs/REGLAS.md` | Las reglas de trabajo con el agente (las que costaron un incidente) |
| `docs/GIT.md` | Cómo se usa git aquí: hooks, commits por rutas, espejos bare, tags, append-only, CI local |
| `docs/INCIDENCIAS_DAG_WIKI.md` | Cómo encajan el tablero de incidencias, el DAG y el wiki repo (canvas/bases) |
| `docs/SEGUNDO_CEREBRO.md` + `docs/PROTOCOLO_SEGUNDO_CEREBRO.md` | El vault Obsidian como memoria compartida (LLM-wiki) y su protocolo |
| `docs/PORTABILIDAD.md` | Qué se reescribe al instalar, qué es opcional, qué no se incluye |
| `skills/` | 21 skills (ver tabla) |
| `esqueleto-repo/` | Archivos listos para copiar a un repo nuevo: hooks, CI, plantillas de issue/PR, `CLAUDE.md`, `RETOMA.md`, `limpiar_entorno.sh`… |
| `ejemplo-qrecauda/` | Un caso real público (repositorio público «qrecauda»): DAG, revisión adversarial, expediente de release, manual de lo pendiente |
| `MANIFIESTO.sha256` | Huella de cada archivo del paquete |

## Skills incluidas

| Grupo | Skills | Para qué |
|---|---|---|
| Plan y estado | `dag-de-proyecto` | El plan como DAG que se valida (ciclos, monotonía, cerrar exige commit con la entrega, una release por revisión adversarial propia…) |
| Documentación viva | `wiki-de-proyecto` | Repo de documentación cuyo árbol de trabajo vive en Obsidian: canvas, bases, tablero de incidencias, histórico de diseños |
| | `wiki-de-empresa` | Wiki corporativa como repo con DAG (plan de negocio, sistemas, revisiones) |
| Segundo cerebro | `llm-wiki`, `vault-ops` | Vault Obsidian que acumula conocimiento; auditoría con cifras (nunca a mano), catálogo, consulta por presupuesto de tokens |
| Principios de código | `code-principles` (enrutador) + `pragmatic-programmer`, `pragmatic-programmer-base`, `clean-architecture`, `domain-driven-design`, `separation-of-concerns`, `functional-immutability`, `defense-in-depth`, `test-driven-development`, `refactoring-clean-code`, `autonomous-loop` | Qué principio cargar en cada situación; auditoría «10/10» con dos lentes y revisión adversarial |
| Proyectos largos | `ariadna` | Sacar un proyecto estancado a prototipo y llevarlo por fases: auditoría, preinscripción, referencia sellada, criterio de delta |
| Cómputo | `corridas-largas-reproducibles` | Corridas caras atribuibles y sin pérdida de horas |
| Respaldo | `repos-espejo`, `archivado-verificable` | Espejos bare; archivado con manifiesto SHA-256 y puerta negativa |
| Escritura | `stop-slop` | Quitar patrones de prosa de IA (en/es, registro académico) |

## Instalación rápida

```bash
unzip metodo-kit.zip && cd metodo-kit
./INSTALAR.sh --ensayo            # ve qué haría
./INSTALAR.sh                     # Claude Code: ~/.claude/skills, vault en ~/segundo-cerebro
./INSTALAR.sh --agente otro --skills ~/metodo-skills --vault /srv/cerebro   # otro agente/servidor
```

Requisitos: `git`, `python3 ≥ 3.10`, `rsync`. Recomendados: `uv`, `gh`. Opcionales: `pandoc`+`xelatex` (papers), `python-pptx` vía `uv run --with python-pptx` (presentaciones), Obsidian (para ver canvas/bases; no es obligatorio para generarlos).
Todo el código de las skills es **stdlib pura de Python**, salvo lo que cada skill declare.

Licencia: Apache-2.0 (ver `LICENSE` y `NOTICE`).

Después: abre `USAGE.md`.
