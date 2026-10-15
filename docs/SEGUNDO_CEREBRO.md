# Segundo cerebro: el vault como memoria compartida

Un vault Obsidian (carpeta de `.md`) que los agentes leen y escriben. Idea (Karpathy/Memex): el conocimiento **se acumula** en notas sintetizadas en vez de re-derivarse por RAG en cada consulta.

## Tres capas
| Capa | Qué | Cómo se usa |
|---|---|---|
| `raw/` | entrada sin curar (volcados, PDFs) | solo con **orden explícita**; no se barre ni se digiere por iniciativa |
| `wiki/` | síntesis: notas atómicas, baratas de leer | el agente lee y edita por iniciativa cuando el trabajo lo pide |
| `alejandria/` | documentos extensos íntegros con catálogo | se entra por `INDICE.md`; un documento a la vez, a petición |

## Reglas duras
- **Síntesis, nunca copia. Una nota, un concepto.** Cifras con fuente y fecha; lo no sabido, `⚠️ sin verificar`; no se borra, se marca obsoleta; el índice se actualiza con la nota.
- **Cifras del vault nunca a mano:** salen de `vault_audit.py` o no se publican.
- **Los mapas tienen presupuesto de tokens** y una compuerta los vigila (un índice que cuesta como lo que mapea deja de servir). Al pasar el techo se parte en sub-mapas.
- **Buscar ≠ orientarse:** `index.md` para «qué existe»; `consulta.py` (≈400 tokens, no crece) para «qué sé de X». El emparejamiento es léxico: usar términos del dominio.
- **Frontmatter:** `tags`, `area` (vocabulario cerrado), `tema` (abierto), `creado`, `actualizado`, `fuente`.
- **Los secretos no viven en el vault.** Carpeta de credenciales aparte; se pasan por ruta.
- Excluir siempre: `.git`, `node_modules`, `.venv`, repos de terceros, archivos de punteros (`.gdoc`…), carpetas de archivo/snapshots.
- **El código no vive en el vault** y las copias de trabajo se editan en un solo sitio; el espejo bare no se edita.

## Herramientas (skills `vault-ops` y `llm-wiki`)
```bash
python3 $SK/vault-ops/scripts/vault_audit.py VAULT          # escala, frontmatter, índice, enlaces rotos, higiene
python3 $SK/vault-ops/scripts/consulta.py "pregunta" --tokens 400 --k 3
python3 $SK/vault-ops/scripts/alejandria_index.py VAULT --escribir   # catálogo, nunca a mano
python3 $SK/vault-ops/scripts/claim_lint.py ...              # ¿el vault se contradice? cifras canónicas
python3 $SK/vault-ops/scripts/esquema_areas.py VAULT [--aplicar]
python3 $SK/vault-ops/scripts/generar_areas.py VAULT
python3 $SK/llm-wiki/local/lint_vault.py VAULT               # grafo: rotos, huérfanas, hubs, componentes
bash    $SK/vault-ops/scripts/certificar.sh                  # compuerta global (sale 1 si algo falla)
```
Respaldo: espejo a un disco **físico distinto** (`respaldo.ps1`/`rsync`); un respaldo en el mismo disco no cuenta.

## Hooks útiles (Claude Code, `settings.json`)
- `SessionStart`: inyectar una **tarjeta de arranque** (≈700 tokens: reglas + dónde está cada cosa), no el mapa entero.
- `PreCompact`: archivar el transcript en la memoria antes de compactar.
- `UserPromptSubmit`: recordar el paso actual del camino crítico (si lo hay).
Ejemplos en la documentación de Claude Code; el protocolo base está en `PROTOCOLO_SEGUNDO_CEREBRO.md`.

## Memoria del agente (auto-memory)
Archivo por hecho, con frontmatter `name/description/type` (`user|feedback|project|reference`) y un `MEMORY.md` índice de una línea por entrada. Se guarda lo no derivable del repo (preferencias, correcciones, decisiones y su porqué); no lo que ya dicen el código o el git. Antes de actuar sobre una memoria que nombra un archivo o flag, se verifica que exista.
