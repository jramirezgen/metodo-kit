# Incidencias, DAG y wiki repo: cómo encajan

Tres piezas, tres preguntas, un solo origen de verdad cada una:

| Pieza | Responde a | Dónde vive | Quién la escribe |
|---|---|---|---|
| **DAG** (`dag-de-proyecto`) | ¿qué hay que hacer y en qué orden? ¿en qué estado está cada cosa? | `plan/construir_dag.py` → `plan/plan.json` (QUÉ) · `registro/nodos.jsonl` (ESTADO, append-only) · `plan/dag.json` (política) | el proyecto; el estado se añade al cerrar con sha |
| **Incidencias** (`wiki-de-proyecto`) | ¿qué decisiones, deudas y hallazgos hay vivos? ¿por qué algo está bloqueado? | `wiki/<PROYECTO>/Incidencias/NN.titulo.md` en la bóveda | **a mano**, en Obsidian |
| **Wiki repo** (`wiki-de-proyecto`) | ¿cómo se ve el sistema de un vistazo? | `docs/wiki/` (intención, versionada) → `wiki/<PROYECTO>/` (árbol de trabajo en la bóveda) | generadores; los mapas se regeneran, no se editan |

## Reglas del DAG (cada una con test que la ve fallar)
1. Sin ciclos ni dependencias inexistentes ni ids repetidos; **una sola hoja** (la release final).
2. Monotonía: nada en curso/bloqueado/cerrado se apoya en lo no cerrado.
3. **Cerrar exige un commit que toque la entrega**; `evidencia` = ese sha.
4. `juzgado` sólo para un eureka, con `veredicto = registro/veredictos.jsonl#<id>`.
5. Cada eureka tiene exactamente **una preinscripción**; sus corridas descienden de ella.
6. Toda corrida/medición declara qué eureka alimenta.
7. **Cada release desciende de una revisión adversarial propia.**
8. Nodos `externo` (otro repo): `entrega = REPO@tag#NODO`; sólo cierra si ese repo, en ese tag, lo da cerrado.
9. Nodos abiertos no citan decisiones congeladas ni frases de alarma; `hecho_cuando` acotado (el plan dice qué; los tests dicen cómo).
10. Los nodos protegidos (corrida, medición, eureka, preinscripción) no se borran ni degradan sin declararlo, comprobado contra toda la historia de `plan.json`.
11. `registro/*.jsonl` y `docs/bitacora/*.md` son append-only.

Tipos de nodo: `infra, doc, dominio, adaptador, insumo, dato, decision, preinscripcion, corrida, medicion, eureka, revision, release, externo`.
Estados usados: `hecho`, `en_curso`, `bloqueado`, `pausado`, `juzgado` (sólo eureka). Ver `ejemplo-qrecauda/nodos.jsonl.muestra` y `ESTADO.md`.

## Incidencias
Una nota por incidencia, con frontmatter:

```yaml
---
situacion: abierta        # abierta | en_curso | bloqueada | resuelta | descartada
peso: media               # libre
hito: ""                  # OBLIGATORIO si resuelta: algo se cierra EN una entrega
bloqueado_por: ""         # OBLIGATORIO si bloqueada, apuntando a otra incidencia que exista
nodo: C.E4                # opcional: nodo del DAG que la sostiene
mapa_n: 1                 # opcional: mapa/nodo del canvas que ancla
---
## Contexto · ## Criterio de aceptación (medible) · ## Intentos
```
`generar_incidencias.py` hace de compuerta (vocabulario cerrado, bloqueo con causa, resuelta con hito) y regenera la Base y el índice. Con `intentos ≥ 2` fallidos, `publicar.py` avisa: se **re-ancla** con auditoría conceptual en vez de insistir.
Puede activarse (`"git_commit_al_cerrar_incidencia": true` en `wiki.json`) que cerrar una incidencia commitee sola el cambio, sólo con las rutas tocadas y sin trailer de modelo.

## Wiki repo: dos mitades
`docs/wiki/` (git: la intención, generadores + `wiki.json` + `wiki.lock.json`) ⟶ `wiki/<PROYECTO>/` (la bóveda: donde se lee y se edita). Se comporta como git: `situacion()` ≈ `git status`; `--adoptar` ≈ `git add`; `publicar.py` ≈ `git checkout` que **se niega a pisar** lo no adoptado; `wiki.lock.json` ≈ `.git/index` (huella canónica y huella de la bóveda).
Estructura en la bóveda: nota puerta `<PROYECTO>.md` · `<TITULAR>/Mapas/*.canvas` numerados `01 — …` · `Versiones/` (histórico) · `Bases/*.base` · `Incidencias/`.
Reglas duras: (0) el tablero de incidencias es la puerta de todo cambio de mapa; (0·bis) objetivo declarado antes de tocar nada; (1) donde se genera no se edita; (2) en la bóveda sí se edita y publicar no lo pisa; (3) ningún diseño anterior se pierde (`archivar.py`); (3·bis) publicar corre los generadores declarados; (4) ninguna cifra se teclea y los huecos se dibujan igual de grandes que lo que funciona; (5) un reporte cerrado en PASS se eleva entero al archivo; (6) cerrar incidencia puede commitear sola.
Se **vendoriza** lo que no tiene política (copiado al repo, con test de divergencia) para que el repo sea autónomo aunque la skill no esté montada. Lo específico del proyecto vive en `wiki.json`.

## Orden de trabajo al tocar un mapa o un diseño
1. Leer `00 — Incidencias de X.md`.
2. Escribir o actualizar la incidencia que lo sostiene.
3. Regenerar el mapa (ya con esa incidencia dentro).
4. Publicar (reindexa en la misma operación).
Un hallazgo medido entra al tablero **antes** que al lienzo: el lienzo es derivado, la incidencia es la fuente.

## Varios repos (AQUERONTE ← ATALANTA ← AJOLOTE)
Un mismo estándar de DAG en cada repo; dependencias entre ellos como nodos `externo` con pin de tag; cada repo con su wiki y su serie `INC-###`; el material de otro repo no se lee por dentro: se consume por su pin, y los mensajes se contestan por incidencias.

## Wiki de empresa
`wiki-de-empresa` aplica lo mismo a una empresa: plan de negocio por bloques como nodos, revisión adversarial por bloque y dossier del primer cliente. `python3 $SK/wiki-de-empresa/scripts/instalar.py --help` y `auditar.py`.
