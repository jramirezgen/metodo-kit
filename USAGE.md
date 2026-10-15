# USAGE — de cero a un proyecto entregado, con los comandos en orden

`$SK` = directorio de skills que elegiste al instalar (`~/.claude/skills` por defecto). Todos los comandos corren desde la raíz del repo.

```bash
export SK=~/.claude/skills        # ajusta si instalaste en otro sitio
```

## 0. Prerrequisitos de la sesión con el agente
1. Que el agente cargue `docs/REGLAS.md` (pégala en su `CLAUDE.md`/`AGENTS.md` global o apúntala desde allí).
2. Credenciales **por ruta**: guarda cada token en `~/.credenciales/<servicio>.txt` (`chmod 600`) y pasa la ruta (`--token-file`). Nunca el valor en un comando, un commit, un log ni un chat.
3. Idioma, estilo y mandatos permanentes del usuario: al `CLAUDE.md` del repo (ver `esqueleto-repo/CLAUDE.md`).

## 1. Crear el repo con su esqueleto
```bash
mkdir mi-proyecto && cd mi-proyecto && git init -b main
cp -r /ruta/metodo-kit/esqueleto-repo/. .            # hooks, CI, plantillas, CLAUDE.md, RETOMA.md…
bash scripts/instalar_hooks.sh                        # git config core.hooksPath scripts/hooks
```
Edita `CLAUDE.md` (3 líneas del proyecto) y escribe `docs/FUNDAMENTO.md`: **objetivo general, objetivo por rama (resuelto/pausado), alcance, reglas, discrepancias declaradas**. Modelo en `ejemplo-qrecauda/EJEMPLO_FUNDAMENTO.md`. Sin objetivo escrito no se sigue (regla 0·bis de `wiki-de-proyecto`).

## 2. Instalar el DAG verificable
```bash
python3 $SK/dag-de-proyecto/scripts/instalar.py . --proyecto MIPROYECTO --hoja REL-0.1.0            # ensayo
python3 $SK/dag-de-proyecto/scripts/instalar.py . --proyecto MIPROYECTO --hoja REL-0.1.0 --aplicar
```
Crea `plan/dag.py`, `plan/dag_lib.py` (vendorizados), `plan/dag.json` (política), `registro/nodos.jsonl` (estado, append-only) y `tests/test_dag_estandar.py`. El plan lo escribes tú en `plan/construir_dag.py` (modelo: `ejemplo-qrecauda/construir_dag.py`), que genera `plan/plan.json` (nunca se edita a mano).
Ciclo de trabajo:
```bash
python3 plan/construir_dag.py            # regenera plan.json
python3 plan/dag.py validar              # reglas 1–11
python3 plan/dag.py siguiente            # qué nodo toca
python3 plan/dag.py estado [--comprobar] # genera/verifica ESTADO.md
```
**Cerrar un nodo** = (1) commit que toque su entrega, (2) añadir una línea a `registro/nodos.jsonl` con `evidencia` = sha de ese commit (ver `ejemplo-qrecauda/nodos.jsonl.muestra`), (3) `dag.py estado`. Cada release desciende de una revisión adversarial **propia** (nodo `tipo: revision`).

## 3. Método por fases (cuando el proyecto es largo o está estancado)
```bash
A=$SK/ariadna/scripts/ariadna.py
python3 $A fase "Fase 1 · nombre"                 # crea docs/mediciones/<fase>/PREINSCRIPCION.md
# …rellena todos los ⟨hueco⟩…
python3 $A sellar  docs/mediciones/<fase>         # se niega si queda un hueco; guarda huella sha256
git add docs/mediciones/<fase> && git commit -m "docs: preinscripción de la fase 1" -- docs/mediciones/<fase>
# …AHORA se corre lo medido…
python3 $A verificar docs/mediciones/<fase>       # ¿la preinscripción cambió tras el sello?
python3 $A cerrar    docs/mediciones/<fase>       # crea RESULTADO.md
python3 $A estado                                  # corre esto al abrir cualquier fase
```
Plantillas en `$SK/ariadna/plantillas/` (AUDITORIA, PREINSCRIPCION, RESULTADO, CRITERIO_DELTA_ESPERADO, hooks).
Regla de oro: **la preinscripción se commitea antes de correr y no se toca después**; el resultado se juzga contra ella aunque salga mal. Para cómputo caro: `$SK/corridas-largas-reproducibles/SKILL.md` antes de lanzar nada.

## 4. Principios de código y auditoría
Invoca `code-principles` (el enrutador) al empezar un módulo, arreglar un bug, refactorizar o antes de declarar algo «10/10». Orden típico: `pragmatic-programmer` → `clean-architecture` → `domain-driven-design` → `separation-of-concerns`; para bugs `test-driven-development` → `defense-in-depth`.
Un diseño no es 10/10 hasta pasar **tres** comprobaciones: lente 1 (principios), lente 2 (mapa de capas + 7 transversales con sitio, regla de imports y test) y **revisión adversarial** por un agente independiente de solo lectura, que lee artefactos y no el chat. Se verifica cada hallazgo contra el texto antes de aceptarlo. Detalle en `$SK/code-principles/SKILL.md`.
Contratos de capas ejecutables: `uv run lint-imports` con un `.importlinter` (modelo: `ejemplo-qrecauda/EJEMPLO.importlinter`).

## 5. Wiki repo: mapas, bases, incidencias
Requiere un vault (carpeta Obsidian). `INSTALAR.sh` crea `~/segundo-cerebro` (o el que indiques con `--vault`).
```bash
S=$SK/wiki-de-proyecto/scripts
python3 $S/iniciar.py . --proyecto MIPROYECTO --vault ~/segundo-cerebro           # ensayo
python3 $S/iniciar.py . --proyecto MIPROYECTO --vault ~/segundo-cerebro --aplicar # estrena docs/wiki/
```
`--area` debe ser una de tus Áreas (por defecto sale «Investigación»; define tu vocabulario cerrado en el protocolo del vault). Esto crea `docs/wiki/` (generadores vendorizados + `wiki.json` + `wiki.lock.json`) y la carpeta `wiki/MIPROYECTO/` en la bóveda. Después:
1. **Escribe la nota puerta** `~/segundo-cerebro/wiki/MIPROYECTO/MIPROYECTO.md` (con `## Objetivo` y `## Marco`). Sin ella, publicar se niega.
2. **Incidencias** (la puerta de todo cambio): una nota por incidencia en `wiki/MIPROYECTO/Incidencias/` con `situacion:` (vocabulario cerrado), `bloqueado_por:` si está bloqueada, `hito:` si resuelta. Se escriben a mano en Obsidian.
3. Escribe tu generador de mapas desde `docs/wiki/plantilla_generador.py` (lee `plan/plan.json`; no teclees cifras) y decláralo en `wiki.json`.
4. Publica:
```bash
python3 docs/wiki/generar_incidencias.py docs/wiki          # tablero + Base + índice (compuerta)
python3 docs/wiki/archivar.py …                              # guarda el diseño vigente en Versiones/ antes de pisarlo
python3 docs/wiki/publicar.py docs/wiki --simulacro          # qué cambiaría
python3 docs/wiki/publicar.py docs/wiki                      # publica; se niega a pisar ediciones manuales no adoptadas
python3 docs/wiki/publicar.py docs/wiki --adoptar            # acepta lo editado a mano en Obsidian
```
Orden obligatorio al tocar un mapa: **leer el tablero → escribir/actualizar la incidencia → regenerar → publicar.** Detalle: `docs/INCIDENCIAS_DAG_WIKI.md`.

## 6. Git, CI y publicación
```bash
bash scripts/ci_local.sh                 # lo mismo que la CI; el hook pre-push lo corre
git add RUTA1 RUTA2 && git commit -m "tipo(ámbito): qué y por qué" -- RUTA1 RUTA2   # por rutas, nunca `git add -A`
git push origin main && git push espejo main
# release: tag anotado + gh release create + CI verde + expediente docs/releases/EXPEDIENTE_<v>.md
```
Convenciones completas (espejos bare, append-only, no reescribir historia): `docs/GIT.md`.

## 7. Segundo cerebro (memoria compartida entre sesiones y agentes)
```bash
python3 $SK/vault-ops/scripts/vault_audit.py ~/segundo-cerebro        # cifras del vault (nunca a mano)
python3 $SK/vault-ops/scripts/consulta.py "pregunta natural" --tokens 400 --k 3
python3 $SK/llm-wiki/local/lint_vault.py ~/segundo-cerebro            # enlaces rotos, huérfanas, hubs
bash    $SK/vault-ops/scripts/certificar.sh                           # compuerta global
```
`INSTALAR.sh` ya deja un vault mínimo con su protocolo. Para sembrar además plantillas (index.md, log.md) en uno NUEVO: `python3 $SK/llm-wiki/scripts/init_vault.py --path ~/segundo-cerebro --topic "…" --help` (léelo antes; en un vault con contenido no lo corras). Protocolo y razones: `docs/SEGUNDO_CEREBRO.md`.

## 8. Cerrar
- Entorno desechable: `bash scripts/limpiar_entorno.sh` (borra `.venv` y cachés del SDK; el SDK nunca se instala global).
- `python3 plan/dag.py estado --comprobar` en verde, `RETOMA.md` actualizado a una página, espejo empujado, token borrado con `shred -u` si era temporal.
- Una sesión nueva debe poder seguir **leyendo sólo** `RETOMA.md` → `ESTADO.md` → `docs/FUNDAMENTO.md`.

## Síntomas frecuentes
| Síntoma | Causa → arreglo |
|---|---|
| `dag.py validar` rechaza cerrar un nodo | el commit no toca la entrega → commitear la ruta de `entrega` y poner ese sha |
| `publicar.py` se niega a escribir | hay edición manual no adoptada → `--adoptar` o revisar la diferencia |
| `commit-msg` rechaza el mensaje | menciona un modelo o trailer de coautoría → quitarlo (regla de no atribución) |
| Test de divergencia falla | la copia vendorizada cambió → `instalar.py <repo> --aplicar` |
| `Unknown skill` | ver los dos nombres posibles en `skills/code-principles/SKILL.md` |
