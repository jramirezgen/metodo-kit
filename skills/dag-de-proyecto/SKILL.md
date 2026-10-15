---
name: dag-de-proyecto
description: "El DAG de un proyecto como contrato verificable — estándar de oro extraído de AQUERONTE (2026-10-05) para AQUERONTE, ATALANTA y AJOLOTE. Usar al planificar un repo, al cerrar o abrir un nodo, al preparar una release, o cuando un plan vive en prosa, en emojis o con el estado editado a mano. Instala `plan/dag_lib.py` + `plan/dag.py` vendorizados con test de divergencia."
---

# dag-de-proyecto — el plan es un DAG que se verifica, no una lista que se cree

Nace de un fallo medido el 2026-10-05: una guarda de AQUERONTE («el adaptador no deja entrar datos
quemados») era **prosa** — el tipo del nodo no exigía ruta y cualquier commit lo cerraba. Y en los repos
hermanos el estado vivía en emojis escritos en el generador (ATALANTA) o editado a mano en el JSON y ya
desfasado del git (AJOLOTE). Esta skill convierte el plan en algo que **muerde**.

## El comando

```bash
S=/mnt/f/skills/_personales/dag-de-proyecto/scripts
python3 $S/instalar.py <repo> --proyecto NOMBRE --hoja REL-1.0.0            # ensayo
python3 $S/instalar.py <repo> --proyecto NOMBRE --hoja REL-1.0.0 --aplicar  # estrena
python3 $S/instalar.py <repo> --aplicar                                     # re-copia SÓLO lo vendorizado

python3 plan/dag.py validar | siguiente | estado [--comprobar]              # dentro del repo
```

## Las tres piezas y quién las escribe

| pieza | qué es | quién |
|---|---|---|
| `plan/construir_dag.py` → `plan/plan.json` | **QUÉ** hay que hacer: nodos, dependencias, entrega, «hecho cuando», qué cubre | el proyecto (nunca a mano el JSON) |
| `registro/nodos.jsonl` | **EN QUÉ ESTADO** está cada nodo: append-only, manda la última línea, con `evidencia` (sha) | se añade una línea al cerrar |
| `plan/dag.json` | la **política** del proyecto: hoja, `requerido`, `congeladas`, `externos`, `alarma` | el proyecto |
| `plan/dag_lib.py`, `plan/dag.py` | las **reglas**, sin política | vendorizado; el test de divergencia vigila la copia |

`ESTADO.md` se genera. El estado **nunca** se edita en el plan: sale del registro, y el registro sólo crece.

## Las reglas (cada una tiene un test que la ve fallar)

1. Sin ciclos, sin dependencias inexistentes, sin ids repetidos; **una sola hoja** (la release final).
2. **Monotonía:** nada `en_curso`, `bloqueado`, `pausado` ni cerrado se apoya en lo no cerrado.
3. **Cerrar exige un commit que toque la entrega** (`evidencia` = sha y el commit toca una ruta de `entrega`).
4. `juzgado` sólo para un eureka, con `veredicto = registro/veredictos.jsonl#<id>`.
5. Cada **eureka** tiene exactamente **una preinscripción**; sus corridas descienden de ella y él depende de una.
6. Toda corrida/medición declara qué eureka alimenta.
7. **Cada release desciende de una revisión adversarial PROPIA** (`tipo: revision`): la que ya sirvió a la
   release anterior no cuenta. Es la regla del usuario «todo avance con su revisión adversarial», hecha código.
8. **Nodos `externo`** (dependencia de otro repo): `entrega = REPO@tag#NODO`, `evidencia = REPO@tag`; sólo
   cierra si ese repo tiene el tag y su registro, **en ese tag**, da el nodo cerrado. Así se encadenan
   AQUERONTE ← ATALANTA ← AJOLOTE sin leer el código del otro.
9. Nodos abiertos: no citan decisiones `congeladas`, ni frases de `alarma`, y `hecho_cuando` ≤ `hecho_max`
   (el plan dice qué; los tests dicen cómo). Un `adaptador` abierto nombra rutas reales.
10. **Protegidos** (corrida, medición, eureka, preinscripción) no se borran, no cambian de tipo ni dejan de
    cubrir su eureka sin declararlo en `degradaciones`, comprobado contra **toda la historia** de `plan.json`.
11. `registro/*.jsonl` y `docs/bitacora/*.md` son append-only, contra cada versión commiteada.
    Desde 2026-10-10 se recorre la línea de primer padre (`--first-parent`): un merge es una transición más y además conserva todas las líneas de su segundo padre (antes, el orden por fecha entrelazaba dos ramas y cualquier merge parecía reescribir el registro).
    Una reescritura ya hecha se exime **sólo** declarándola en `dag.json` → `rectificadas: {"ruta@sha7": "motivo"}` (motivo obligatorio; vale para esa ruta en ese commit y nada más), y `dag.py validar` la lista en su salida.
    git **falla cerrado**: sin repo, con un objeto perdido o un sha ilegible, la comprobación lanza `GitRoto` y `validar` sale con error; un repo sin commits no es un repo roto.

## Tipos de nodo

`infra`, `doc`, `dominio`, `adaptador`, `insumo`, `dato`, `decision`, `preinscripcion`, `corrida`,
`medicion`, `eureka`, `revision`, `release`, `externo`. El vocabulario de tipos es abierto salvo los que
tienen regla.

## Cómo se migra un repo que ya tiene plan

- **AQUERONTE** es el origen: su `plan/reglas.py` añade reglas propias (REQUERIDO de su arquitectura,
  `SECCIONES_ARQ`). Migrarlo es hacer de `reglas.py` un envoltorio fino sobre `dag_lib` con los tests verdes.
- **ATALANTA** (DAG escrito a mano en `generar_dag_pipeline.py`, estado en emoji) y **AJOLOTE**
  (`docs/plan/v2.23.0/plan.json` con estado a mano): se traduce su plan a `construir_dag.py`, su estado
  actual a líneas del registro con su sha, y sus revisiones (R1, R2…) a nodos `revision` delante de cada
  release. El mapa del wiki se genera desde `plan.json` (ver `wiki-de-proyecto`).

## Lo que NO hace (declarado)

- No dibuja el canvas: eso es `wiki-de-proyecto`, que lee el mismo `plan.json`.
- No sabe de veredictos de juez más allá del ancla: el esquema de `veredictos.jsonl` es de cada proyecto.
- No decide qué es una revisión adversarial suficiente: exige que **exista** como nodo cerrado con su
  commit; el contenido lo fija `code-principles` («un 10/10 se audita con dos lentes y un tercero»).
