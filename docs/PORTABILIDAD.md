# Portabilidad

## Qué reescribe `INSTALAR.sh`
Las skills se escribieron en un equipo con rutas fijas. Al instalar, en los archivos copiados:

| Ruta original | Se sustituye por | Flag |
|---|---|---|
| `/mnt/f/skills/_personales`, `/mnt/f/skills` | el directorio de skills | `--skills` |
| `/mnt/f/OBSIDIAN` | tu vault (segundo cerebro) | `--vault` |
| `/mnt/f/src/api/api` | carpeta de credenciales (fuera de todo repo, modo 700) | `--cred` |

Rutas de Windows que quedan en texto (`F:\...`, `G:\...`) son **ejemplos de infraestructura del equipo original** (discos de espejo y respaldo): sustitúyelas por las tuyas al leer `repos-espejo`, `vault-ops` (`respaldo.ps1`) y `archivado-verificable`.

## Qué es específico del equipo original y puedes ignorar
- `vault-ops/scripts/notion_*.py`: sincronizar un workspace de Notion al vault. Útil sólo si migras desde Notion; el token se pasa **por ruta** (`--token-file`).
- `vault-ops/amadeus/` y `mcp_server.py`: acceso al vault desde un modelo local por MCP.
- Nombres como SAPYRIA, TGDE, ELEMENT en ejemplos de las skills: son casos reales usados como ilustración.
- `sapyria-*`, ciencia (bio, quimica…): **no incluidos**; el kit es de método, no de dominio.
- `wiki-de-personas` **no se incluye** a propósito (maneja datos personales de terceros).

## Autoría
Las skills propias llevan `autor: Kaitokid` (seudónimo) en el frontmatter. Conserva el crédito si redistribuyes; `stop-slop` es MIT (hardikpandya/stop-slop); `llm-wiki` es MIT (claude-code-skills).

## Otros agentes (no Claude Code)
Una skill es un `SKILL.md` con frontmatter (`name`, `description`) más scripts. Cualquier agente que lea archivos puede seguirla: apunta su archivo de instrucciones (`AGENTS.md`, reglas de Cursor, etc.) a `docs/REGLAS.md` y a la tabla de skills, y que lea el `SKILL.md` correspondiente antes de actuar. Los scripts se ejecutan igual desde cualquier shell.

## Lo que NO cubre el kit
- No trae credenciales de nada. Cada servicio (GitHub, IBM, Notion…) se configura con su propio login y se entrega a los scripts **por ruta**.
- No decide si una revisión adversarial es suficiente: exige que exista; el contenido lo fija `code-principles`.
- No sustituye el juicio: las compuertas detectan lo que alguien ya sufrió; un fallo nuevo seguirá siendo nuevo.
