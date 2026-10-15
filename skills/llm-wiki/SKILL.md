---
name: llm-wiki
description: Use when building or maintaining a persistent personal knowledge base (second brain) in Obsidian where an LLM incrementally ingests sources, updates entity/concept pages, maintains cross-references, and keeps a synthesis current. Triggers include "second brain", "Obsidian wiki", "personal knowledge management", "ingest this paper/article/book", "build a research wiki", "compound knowledge", "Memex", or whenever the user wants knowledge to accumulate across sessions instead of being re-derived by RAG on every query. En este equipo el vault ya existe (/mnt/f/OBSIDIAN) y manda su protocolo: usar esta skill para AUDITAR EL GRAFO (enlaces rotos, huerfanas, hubs, componentes) con local/lint_vault.py; para cifras del vault usar vault-ops, para canvas y bases usar wiki-de-proyecto, y NUNCA correr aqui init_vault.py ni update_index.py.
context: fork
license: MIT
version: 1.0.0
author: claude-code-skills
tags:
  - knowledge-management
  - obsidian
  - second-brain
  - pkm
  - rag-alternative
  - wiki
  - karpathy
  - memex
compatible_tools:
  - claude-code
  - codex-cli
  - cursor
  - antigravity
  - opencode
  - gemini-cli
metadata:
  mcpmarket-version: 1.0.0
---
# LLM Wiki — Second Brain for Claude Code + Obsidian

## ⚠️ Adaptación local — leer ANTES de correr cualquier script

> Esta sección la añadió el 2026-09-09 la instalación en este equipo. Lo que hay
> debajo de ella es el texto original de la skill, intacto, y describe un vault
> **recién creado**. El de aquí, `/mnt/f/OBSIDIAN`, lleva funcionando desde el
> 2026-07-26, tiene su propio protocolo autoritativo en `/mnt/f/OBSIDIAN/CLAUDE.md`
> y **su propia arquitectura de mapas**. Las dos cosas conviven; ninguna sustituye
> a la otra.

### Los mapas son ficheros, y no los hace esta skill

La skill `wiki-de-proyecto` publica **JSON Canvas (`.canvas`)** y **bases nativas
de Obsidian (`.base`)** dentro de la bóveda, generadas desde el repo de cada
proyecto. Se enlazan como cualquier nota. Esa es la arquitectura de canvas y **no
se toca**: un mapa no se edita donde se lee, se regenera desde su `wiki.json`.

`scripts/lint_wiki.py` no sabe que existen. Medido el 2026-09-09 sobre este vault:

| Comprobación del linter original | Dio | De los que eran reales |
| --- | ---: | ---: |
| enlaces rotos | 554 | **11** |
| notas sin frontmatter | 706 de 706 | **1** |

El 98 % de falsos sale de tres supuestos que aquí no se cumplen: que todo destino
vive en `wiki/` (aquí también en `alejandria/` y en la raíz), que todo destino es
`.md` (aquí también `.canvas` y `.base`), y que el frontmatter es
`title/category/summary` (aquí es `area:`/`tema:`).

**Por eso el linter que se usa aquí es `local/lint_vault.py`**, que resuelve las
tres cosas y deja el de origen sin tocar para poder actualizarlo limpio:

```bash
python3 /mnt/f/skills/_personales/llm-wiki/local/lint_vault.py           # /mnt/f/OBSIDIAN
python3 /mnt/f/skills/_personales/llm-wiki/local/lint_vault.py --json
```

### Qué script se puede correr aquí y cuál no

| Script | Contra `/mnt/f/OBSIDIAN` |
| --- | --- |
| `local/lint_vault.py` | **Sí.** Es el linter de este vault. Solo lectura |
| `scripts/graph_analyzer.py` | **Sí.** Solo lectura. Aporta lo que `vault_audit.py` no da: hubs, sumideros y componentes débiles del grafo |
| `scripts/export_marp.py` | **Sí**, escribiendo fuera de la bóveda |
| `scripts/wiki_search.py` | Redundante. Aquí se busca con `vault-ops/scripts/consulta.py`, que además recorre el grafo curado y trae la respuesta dentro de un presupuesto de tokens fijo |
| `scripts/lint_wiki.py` | Solo para un vault ajeno. Aquí da 98 % de falsos (tabla de arriba) |
| `scripts/append_log.py` | Exige `wiki/log.md`, que aquí no existe. La cronología vive en las bitácoras de cada proyecto |
| `scripts/ingest_source.py` | **Solo bajo orden explícita.** Lee `raw/`, y `raw/` la exige |
| `scripts/update_index.py` | ⛔ **Prohibido.** Escribiría `wiki/index.md`, un segundo índice que competiría con el maestro de la raíz y con sus sub-mapas (`index_TGDE.md`, `index_NOVEDADES.md`), y aplanaría la jerarquía que existe justo para que el mapa quepa en el contexto |
| `scripts/init_vault.py` | ⛔ **Prohibido.** Sembraría `CLAUDE.md` y `AGENTS.md` de plantilla encima de los autoritativos |

### Cuál de las cuatro skills de bóveda toca

| La pregunta es… | La skill es |
| --- | --- |
| ¿cuántas notas, cuántos tokens, qué falta indexar, qué cifra publico? | **`vault-ops`**. Las cifras del vault salen de su script o no salen |
| quiero ver un pipeline entero de un vistazo; un canvas, una base, un tablero de incidencias | **`wiki-de-proyecto`** |
| voy a consolidar un resultado técnico y tiene que quedar mecanístico y verificado | **`wiki-mecanistico-robusto`** |
| el grafo: qué está huérfano, qué enlace no resuelve, qué nota nadie enlaza | **esta** (`llm-wiki`), por `local/lint_vault.py` |

Esta skill **no manda sobre cómo se opera el vault**. Eso lo hace
`/mnt/f/OBSIDIAN/CLAUDE.md`, y ante cualquier choque gana él.


Inspired by Andrej Karpathy's LLM Wiki pattern ([gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)). This skill turns Claude Code (or any agent CLI) into a disciplined wiki maintainer that **incrementally builds and maintains** a persistent, interlinked Obsidian vault as you feed it sources. The knowledge compounds — cross-references, contradictions, and synthesis are already there when you query.

## Core principle

Most LLM+docs workflows are **RAG**: retrieve fragments at query time, synthesize from scratch, forget. The wiki is **compounding**: sources are read once, integrated into a persistent markdown knowledge base, and kept current. You curate and ask; the LLM reads, files, cross-references, and maintains.

> Obsidian is the IDE. The LLM is the programmer. The wiki is the codebase.

## When to use

- **Personal**: track goals, health, psychology, journaling, self-improvement
- **Research**: deep dives over weeks on a topic — papers, articles, reports, evolving thesis
- **Book companion**: file chapters as you read; build a fan-wiki-style companion for characters, themes, plot threads
- **Business/team**: internal wiki fed by Slack, meeting notes, calls — LLM does maintenance nobody else wants to do
- **Competitive analysis, due diligence, trip planning, course notes, hobby deep-dives**

**Do NOT use when:** you need one-shot Q&A over a fixed document (use RAG), you don't plan to add sources over time, or you don't want Obsidian in the loop.

## Architecture (three layers)

```
vault/
├── raw/                    # Layer 1 — IMMUTABLE source of truth
│   ├── <source files>      # Articles, papers, PDFs, images, data
│   └── assets/             # Downloaded images from clipped articles
├── wiki/                   # Layer 2 — LLM-owned knowledge base
│   ├── index.md            # Content catalog (LLM updates every ingest)
│   ├── log.md              # Append-only timeline (## [YYYY-MM-DD] <op> | <title>)
│   ├── entities/           # Person/Org/Place pages
│   ├── concepts/           # Ideas, theories, frameworks
│   ├── sources/            # One summary page per ingested source
│   ├── comparisons/        # Cross-source analysis pages
│   └── synthesis/          # High-level syntheses, theses, overviews
├── CLAUDE.md               # Schema + conventions (Claude Code)
└── AGENTS.md               # Same content, for Codex/Cursor/Antigravity
```

- **Layer 1 (raw/)** — you own. LLM only reads; never writes.
- **Layer 2 (wiki/)** — LLM owns. It creates, updates, and cross-references pages. You read it.
- **Layer 3 (CLAUDE.md / AGENTS.md)** — the *schema*. Conventions, workflows, frontmatter rules. Co-evolved by you and the LLM.

## Three core operations

1. **Ingest** — LLM reads a source, discusses takeaways with you, writes a source summary, updates 10-15 relevant pages, updates index, appends to log. See `references/ingest-workflow.md`.
2. **Query** — LLM reads `index.md` first, drills into relevant pages, synthesizes with citations. Good answers get **filed back into the wiki** so explorations compound. See `references/query-workflow.md`.
3. **Lint** — Health check: contradictions, stale claims, orphan pages, missing cross-refs, concepts mentioned but lacking their own page, data gaps to fill with web search. See `references/lint-workflow.md`.

## Quick start

```bash
# 1. Initialize a vault (in Obsidian's vault directory)
python scripts/init_vault.py --path ~/vaults/research --topic "LLM interpretability"

# 2. Drop a source into raw/, then ingest
/wiki-ingest ~/vaults/research/raw/anthropic-monosemanticity.pdf

# 3. Ask questions (answers can be re-filed into the wiki)
/wiki-query "how does monosemanticity compare to mechanistic interpretability?"

# 4. Periodic health check
/wiki-lint

# 5. See the timeline
/wiki-log --last 10
```

## Slash commands (this plugin ships)

| Command | Purpose |
|---|---|
| `/wiki-init` | Bootstrap a fresh vault with schema files + starter structure |
| `/wiki-ingest <path>` | Read a source, discuss, update wiki, log it |
| `/wiki-query <question>` | Search wiki, synthesize answer, offer to file back |
| `/wiki-lint` | Run health check — contradictions, orphans, stale claims, gaps |
| `/wiki-log` | Show recent log entries (uses unix tools on `log.md`) |

## Sub-agents (this plugin ships)

| Agent | When dispatched |
|---|---|
| `wiki-ingestor` | Delegated ingest flow — reads source, proposes updates, applies after your approval |
| `wiki-linter` | Runs the health-check workflow independently, reports findings |
| `wiki-librarian` | Answers queries using index-first search, synthesizes with citations |

## Python tools (`scripts/`)

All tools are **standard library only** (no pip installs). Run with `python scripts/<tool>.py --help`.

| Script | Purpose |
|---|---|
| `init_vault.py` | Create folder structure + seed CLAUDE.md, AGENTS.md, index.md, log.md |
| `ingest_source.py` | Helper: extract text/frontmatter from a source file, ready for LLM review |
| `update_index.py` | Regenerate `index.md` from wiki page frontmatter (category, date, source count) |
| `append_log.py` | Append a standardized log entry `## [YYYY-MM-DD] <op> \| <title>` |
| `wiki_search.py` | BM25 search over wiki pages (standalone fallback when index.md isn't enough) |
| `lint_wiki.py` | Find orphans (no inbound links), stale pages, missing cross-refs, broken links |
| `graph_analyzer.py` | Compute link graph stats — hubs, orphans, clusters, disconnected components |
| `export_marp.py` | Render a wiki page (or subtree) to a Marp slide deck |

## Cross-tool compatibility

The vault's **schema** lives in CLAUDE.md (Claude Code) or AGENTS.md (Codex/Cursor/Antigravity/OpenCode). The same content works in both. This plugin ships both templates. For per-tool setup instructions see `references/cross-tool-setup.md`.

```
CLAUDE.md       → Claude Code
AGENTS.md       → Codex CLI, Cursor, Antigravity, OpenCode, Gemini CLI
.cursorrules    → legacy Cursor (pre-AGENTS.md)
```

The scripts are pure Python stdlib → run identically everywhere. Only the loader file changes per tool.

## Obsidian setup (recommended)

- **Obsidian Web Clipper** — browser extension; converts web articles to markdown and drops them in `raw/`
- **Download images locally** — Settings → Files and links → Attachment folder path = `raw/assets/`. Settings → Hotkeys → bind "Download attachments for current file" to `Ctrl+Shift+D`
- **Graph view** — see hubs/orphans; essential for spotting structural problems
- **Marp plugin** — Markdown-based slide decks directly from wiki pages
- **Dataview plugin** — dynamic tables/lists over page frontmatter (tags, dates, source counts)
- **Git** — the vault is a plain markdown repo; version it

Full setup walkthrough: `references/obsidian-setup.md`

## Why this works (vs plain RAG)

| Plain RAG | LLM Wiki |
|---|---|
| Rediscover knowledge each query | Knowledge accumulates |
| Cross-references re-computed every time | Cross-references pre-written and maintained |
| Contradictions surface only if you ask | Contradictions flagged during ingest |
| Exploration disappears into chat history | Good answers re-filed as new pages |
| Scales by embeddings infrastructure | Scales by markdown + `index.md` + optional local search |

At ~100 sources / hundreds of pages, `index.md` + filesystem search is enough. Past that, layer in a local search tool like [qmd](https://github.com/tobi/qmd) or use `scripts/wiki_search.py`.

## Related skills (chains via `context: fork`)

This skill is marked `context: fork` so other skills can chain into it:

- **`para-memory-files`** — PARA-method memory; complementary as long-term personal memory that feeds sources into the wiki
- **`obsidian-vault`** (mattpocock) — lightweight Obsidian note helper; this skill is the maintained-wiki layer on top
- **`rag-design`** — when wiki outgrows ~500 pages, use rag-design to bolt on a retrieval layer
- **`mcp-design`** — expose the wiki as an MCP tool
- **`agent-communication`** — for multi-agent wiki maintenance (ingestor + linter + librarian)

## Reference docs

- `references/wiki-schema.md` — full vault layout, page frontmatter, naming conventions
- `references/page-formats.md` — entity, concept, source, comparison, synthesis templates
- `references/ingest-workflow.md` — the detailed ingest flow the wiki-ingestor agent follows
- `references/query-workflow.md` — query patterns, citation format, re-filing answers
- `references/lint-workflow.md` — health-check heuristics
- `references/obsidian-setup.md` — Obsidian plugins, hotkeys, vault config
- `references/cross-tool-setup.md` — per-tool setup (Codex, Cursor, Antigravity, etc.)
- `references/memex-principles.md` — Bush's Memex, why the LLM changes the maintenance math

## Templates (`assets/`)

- `CLAUDE.md.template`, `AGENTS.md.template`, `.cursorrules.template` — schema loaders per tool
- `index.md.template`, `log.md.template` — starter index and log
- `page-templates/` — entity, concept, source-summary, comparison, synthesis
- `example-vault/` — small worked example you can study or copy

## Iron rule

**The LLM never edits files in `raw/`.** Ever. Sources are immutable. All LLM writes go to `wiki/`. If you need to correct a source, do it in `raw/` yourself — then re-ingest.
