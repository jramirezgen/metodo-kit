# Git: cómo se usa aquí (y por qué es «curioso»)

Git no es sólo control de versiones: es el **libro de contabilidad** del proyecto. El registro cita shas; las reglas del DAG comprueban contra la historia. Por eso las convenciones son más estrictas de lo habitual.

## 1. Commits
- **Por rutas concretas:** `git add ruta1 ruta2 && git commit -m "…" -- ruta1 ruta2`. Con `-- <rutas>` el commit no se lleva lo que otro dejó preparado. Jamás `git add -A` / `commit -a`.
- Mensaje: `tipo(ámbito): qué y por qué` (`feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `release`). Idioma del proyecto.
- **Sin atribución a modelos.** Hook `scripts/hooks/commit-msg` (incluido en `esqueleto-repo/`): rechaza trailers `Co-authored-by/Assisted-by/Generated-by`, menciones a modelos y marcas de herramienta. La misma regla se aplica al `git log` desde un test de arquitectura (`tests/arquitectura/test_sin_atribucion.py` en QRECAUDA), de modo que un `--no-verify` también se detecta en CI.
- **Cerrar un nodo del DAG = un commit que toque su entrega.** Ese sha es la `evidencia` del registro.

## 2. Hooks
```bash
bash scripts/instalar_hooks.sh      # git config core.hooksPath scripts/hooks (versionados con el repo)
```
- `commit-msg`: no atribución.
- `pre-push`: corre `scripts/ci_local.sh` (ruff, mypy, lint-imports, validación del DAG, tests). Con la CI en rojo no sale el push.
- (Opcional) `pre-commit` antisecretos; plantillas en `skills/ariadna/plantillas/hooks/`.
- Los hooks dentro de tests que crean repos git deben limpiar las variables `GIT_*` heredadas del hook (si no, un `git init` de prueba cae en el repo real).

## 3. Historia y registros
- **La historia no se reescribe** (rebase/filter-branch/amend sobre lo publicado): rompería los sha de `registro/`. Si se publicó algo que no debía, se corrige hacia delante y se declara.
- `registro/*.jsonl` y `docs/bitacora/*.md` son **append-only**; la regla 11 del DAG lo comprueba contra cada versión commiteada. Manda la última línea de cada nodo.
- En repos con ramas de trabajo: las ramas commitean código; el `registro/` se escribe **sólo en `main` tras el fast-forward**, para que los sha existan donde se citan.

## 4. Remotos y respaldo
| remoto | para qué |
|---|---|
| `origin` | publicación (GitHub). Credencial con `gh auth login`, nunca token en URL |
| `espejo` | repo **bare** en otro disco: respaldo del historial; **no se edita** (por eso no puede divergir) |

```bash
git init --bare /ruta/otro-disco/espejos/MIPROYECTO.git
git remote add espejo /ruta/otro-disco/espejos/MIPROYECTO.git
git push origin main && git push espejo main
```
Nunca se crea una segunda copia de trabajo para «respaldar»: divergió tres veces. Respaldar = `git push espejo --all`. Skill `repos-espejo` refresca todos los espejos; `archivado-verificable` retira workspaces con manifiesto SHA-256.

## 5. Tags y releases
- Un release **por hito** (cierre de bloque), no por commit. Tag anotado `vX.Y.Z`, `gh release create` con notas **sin** atribución, CI verde.
- Cada release lleva `docs/releases/EXPEDIENTE_<v>.md` (alcance · arquitectura · cómo se probó · resultados con script que los reproduce · despliegue · deuda abierta) y desciende de una revisión adversarial propia (nodo `revision` del DAG).
- Antes de empujar un release: `./scripts/ci_local.sh` y `python3 plan/dag.py estado --comprobar`.

## 6. Ramas y worktrees
- Corridas largas o ensayos en paralelo: `git worktree add ../MIPROYECTO_xx rama`; al terminar, `ff` a main y borrar el worktree.
- Un reinicio de máquina puede corromper objetos recién escritos: tras un corte, `git fsck` antes de seguir y empujar pronto.

## 7. Incidencias de GitHub / PR
Plantillas en `esqueleto-repo/.github/` (bug, propuesta, PR). Los **repos se hablan por incidencias**: un mensaje de otro repo se contesta en la misma incidencia; las dependencias entre repos se modelan como nodos `externo` del DAG (`REPO@tag#NODO`), que sólo cierran si ese repo tiene el tag y su registro lo da cerrado.
