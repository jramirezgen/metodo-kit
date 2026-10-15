---
name: ariadna
description: "Método para proyectos LARGOS (semanas o meses, varias sesiones y agentes): cómo sacar un proyecto ESTANCADO a un prototipo funcional y llevarlo por fases hasta producción sin perder el hilo. Úsala cuando un proyecto da vueltas sin cerrar nada, cuando hay que decidir qué hacer primero en un repo con deuda, antes de un refactor grande, antes de cambiar comportamiento de algo que ya funciona, al planear un release (v0.0.1 → v0.1.0 → 1.0), al montar CI/hooks sobre una referencia sellada, o cuando haya que redactar una auditoría, una preinscripción de fase o un informe de resultado. Trae el script `ariadna.py` (fase/sellar/verificar/cerrar/estado) y plantillas de auditoría, preinscripción, resultado, criterio de delta y hooks. Cada regla lleva el incidente que la costó."
metadata:
  version: 1.0.0
  autor: "Kaitokid"
  creado: 2026-09-23
---

# ariadna — el hilo para salir del laberinto de un proyecto largo

Teseo no salió del laberinto por ser fuerte: salió porque Ariadna le dio un hilo
atado a la entrada. En un proyecto largo, el laberinto es la suma de sesiones,
agentes y decisiones que nadie recuerda dos días después. **El hilo es lo que se
deja en el disco**: auditoría, preinscripciones con huella, una referencia
sellada, incidencias y trinquetes. Una sesión nueva puede seguirlo sin preguntar
nada.

Esta skill destila cómo ATALANTA pasó de fases que no cerraban a un
prototipo sellado. Una vez sellado, hizo en un solo día (2026-09-23) la auditoría,
la Fase 0 y la Fase 1 hacia producción, sin mover un bit de la referencia. No es
teoría de gestión: es la lista de lo que funcionó y de lo que rompió, con su cifra.

**Complementarias, no sustitutas:** `wiki-de-proyecto` (tablero de incidencias y
mapas), `corridas-largas-reproducibles` (cómputo caro atribuible) y
`pragmatic-programmer` (artesanía del código). `fase-sellada-principia` es la
versión de repositorio de esta misma idea, atada a PRINCIPIA.

## La herramienta (primero esto)

```bash
A=/mnt/f/skills/_personales/ariadna/scripts/ariadna.py   # desde la raíz del repo
python3 $A fase "Fase 1 · arreglos baratos"   # crea docs/mediciones/fase_1_arreglos_baratos_<fecha>/PREINSCRIPCION.md
python3 $A sellar docs/mediciones/fase_1_arreglos_baratos_<fecha>     # se niega si queda algún ⟨hueco⟩
python3 $A verificar docs/mediciones/fase_1_arreglos_baratos_<fecha>  # ¿cambió la preinscripción desde el sello?
python3 $A cerrar docs/mediciones/fase_1_arreglos_baratos_<fecha>     # verifica y crea RESULTADO.md
python3 $A estado                                  # todas las fases: sellada/SIN SELLO/HUELLA ROTA, abierta/cerrada
```

Salidas: 0 bien, 1 algo no cuadra (lo nombra), 2 uso.

`estado` y `verificar` reconocen también las convenciones anteriores a esta skill:
- cualquier `*.sha256` que se llame `…preinscrip…` o que cubra un fichero con ese
  nombre, porque a veces la preinscripción es el propio script;
- una serie versionada (`.v1`, `.v2`…) se juzga por su última versión.

Probado sobre ATALANTA el 2026-09-23: 33 carpetas con preinscripción, 5 selladas, **y
una HUELLA ROTA real**. `verif_sello_2026-09-23/PREINSCRIPCION.sha256` sellaba también
`a4_k1.py`, que ya no coincide y que su `RESULTADO.md` no menciona. Por eso `estado` se
corre al abrir cualquier fase.

Plantillas en
`/mnt/f/skills/_personales/ariadna/plantillas/`: `AUDITORIA.md`,
`PREINSCRIPCION.md`, `RESULTADO.md`, `CRITERIO_DELTA_ESPERADO.md` y
`hooks/{pre-commit,pre-push}`.

## El camino, en seis etapas

### Etapa 0 — Declarar el objetivo y el ENTREGABLE (el desatasco más barato)

Un proyecto se estanca casi siempre porque persigue un umbral que no puede alcanzar,
o un objetivo que nunca se escribió. Antes de medir nada más:

- **Escribir el objetivo general** y uno por rama, cada uno **resuelto** o
  **pausado**. Nunca olvidado (regla 0·bis de `wiki-de-proyecto`).
- **Nombrar el entregable.** En ATALANTA, lo que desatascó el proyecto el 2026-09-23
  fue cambiar de qué era el producto: *las ómicas son entrada; el producto es la
  tabla de pesos y las rutas*. Con ese cambio, el lazo que ya existía pasó a ser el
  prototipo.
- **Un umbral que el propio dato no alcanza garantiza el FALLA por construcción.**
  Ejemplo: 74,5 % de dirección medida contra un umbral más alto. Un bloque así queda
  **diagnosticado, no cerrado**. Se declara el techo y se cambia la pregunta; no se
  relaja el umbral a escondidas.

### Etapa 1 — Diagnosticar los bloqueos con evidencia, no con intuición

| antes de declarar… | se mide… | lo que costó no hacerlo |
|---|---|---|
| «bloqueado por un insumo externo» | tamaño, contenido, reintento con otra vía, status HTTP citado | bloqueos falsos que paran fases enteras |
| «falta el dato X» | la **sensibilidad** del resultado a X | el nodo más sensible (S = 0,50) aún pedía ×345,8: el hueco no era la explicación |
| «falta palanca» | **apagar ramas** para ver dónde va el flujo | una represión de 807× no movía nada porque otra rama llevaba el 95 % |
| «no existe / está apagado» | config + tablero + `git log`; grep con el **vocabulario del repo** | «el motor no tiene medio»: `medio.py` llevaba dos días vivo, sin llamar |
| «la campaña necesita más N» | una stopping rule **declarada antes** de gastar | campañas completadas por inercia |

**Nunca se entrega un «no se puede» a secas.** Cada bloqueo sale con su
alternativa, que logre el objetivo entero o la parte que sí se puede.

### Etapa 2 — El prototipo: una corrida de punta a punta, SELLADA

El prototipo no es «el código funciona». Es **una corrida completa cuyo resultado
queda congelado como referencia funcional**:

1. Correrla en una carpeta propia y fechada, con su preinscripción.
2. **Sellar**: `SELLO_REFERENCIA.sha256` con las huellas de los artefactos, y una copia
   versionada de todo insumo que no esté en git. En ATALANTA el GEM no tenía historia
   en ningún sitio: se versionó como `.gz` con su sha.
3. **Escribir un comparador** con tres veredictos: **IDÉNTICO** (0), **MEJORA** (2) y
   **REGRESIÓN** (1). Y **avisos** que no bloquean, para lo que varía entre brazos
   equivalentes: dos brazos iguales ya diferían en 41 reacciones periféricas. Si eso
   cuenta como regresión, la compuerta grita en cada corrida y se acaba ignorando.
4. **Probar que el comparador muerde**: un brazo equivalente pasa, un peso mutado falla
   y un J cambiado falla. Un comparador sin casos que muerden no compuerta nada.
5. Declarar la regla: **cualquier cambio que rompa la referencia es una regresión,
   no una mejora**, salvo que se declare y se re-selle con preinscripción nueva.

### Etapa 3 — v0.0.1: publicar limpio lo que ya funciona

- **Fork limpio**, sin el historial heredado, con un **trinquete** que falla si el código
  vuelve a citar el proyecto del que salió. Ojo: un trinquete así se caza a sí mismo
  si alguien escribe el nombre «para negarlo».
- **Remotos declarados:** a cuál se empuja y a cuál no se empuja nunca. Nunca
  `push --tags` ni `push -f` sin orden expresa.
- **El release va con su informe** (arquitectura, método, resultados, validación). Un
  CHANGELOG no basta. Ajustado 2026-09-27: ese informe no es un paper
  académico — es un **expediente técnico profesional**
  (`docs/releases/EXPEDIENTE_<version>.md`) que consolida la evidencia (tests,
  reproducibilidad, comparación contra el baseline, cómo desplegar) de que el
  prototipo llegó al nivel defendible para producción; ver
  `[[releases-van-con-su-paper]]`. El objetivo de la Etapa 5 sigue siendo el
  mismo: **llegar** a ese nivel — el expediente sólo lo deja constatado, no lo
  sustituye.

### Etapa 4 — Auditoría de SÓLO LECTURA antes de mejorar nada

Plantilla `AUDITORIA.md`. No se toca código. Produce:

- una **lista de deficiencias** con fichero:línea, alcance medido (recuentos, no
  adjetivos), clase (**P** bloquea producción · **V** validez · **R** robustez ·
  **E** estética) y coste (S/M/L, con el porqué);
- el **hallazgo estructural que reordena el plan**. En ATALANTA: «hay dos motores».
  El lazo aplicaba física que sólo vivía en `docs/`, así que cualquier arreglo en
  `src/` rompería el sello;
- los **bloqueos con su alternativa**, y los **choques de órdenes** señalados para que
  decida el usuario. Ejemplo: «CI en GitHub» contra «sin push hasta la Fase 5»;
- el **triaje de incidencias viejas**: se proponen *pausadas por cambio de objetivo*,
  no obsoletas. Decide el usuario.

### Etapa 5 — Fases hacia producción: primero lo que NO cambia comportamiento

El orden que funcionó, y por qué:

| fase | qué | criterio | por qué va ahí |
|---|---|---|---|
| 0 | **refactor puro**: lo que vive en `docs/` o en scripts sube al paquete | **IDÉNTICO**. Si rompe el sello, es **bug del traslado**, no hallazgo | así los arreglos siguientes tocan un solo motor y cada re-sellado se hace una vez, no dos |
| 1 | **arreglos baratos sin comportamiento**: insumos versionados con sha y aborto, tests que no leen fuera del repo, CI, hooks, criterio de delta | IDÉNTICO + suite verde en cada entorno | es la red de seguridad que la Fase 2 va a necesitar |
| 2 | **cambios de comportamiento**, uno por brazo | delta esperado, escrito **antes** (`CRITERIO_DELTA_ESPERADO.md`) | coincide → re-sello; no coincide → hallazgo |
| 3 | **integración** (conectar piezas, generalizar) | end-to-end | depende de un motor ya limpio |
| 4 | **robustez** (tests unitarios, huecos del comparador) | cobertura declarada | — |
| 5 | **release**: push, CI estrenado, tag | todo lo anterior verde | el push llega al final, no antes |

**El primer cambio de comportamiento es el que tiene la evidencia cuantitativa más
fuerte**, no el más urgente. Ejemplo: una constante genérica daba 1,3 µM e⁻/h frente
a 49,21 con la forma elemental, ×38.

## El protocolo de CADA fase (no tiene atajos)

1. **Tablero primero**: leer las incidencias y anclar la fase a la que sostiene.
2. `ariadna.py fase` → rellenar la preinscripción → `ariadna.py sellar` →
   **commit de la preinscripción sola**, antes de tocar código.
3. Ejecutar. Guardar un log por criterio en la carpeta de la fase. **Criterios
   conjuntivos**: fallar uno es fallar la fase. Nunca se describe un nivel bajo como
   si fuera uno alto.
4. Si algo sale mal a mitad: arreglarlo y **repetir desde el primer criterio**, no
   desde donde falló.
5. `ariadna.py cerrar` → `RESULTADO.md` con cinco apartados:
   - el veredicto, con la evidencia por fila;
   - lo que no salió a la primera y qué era;
   - los hallazgos que nadie había visto;
   - las **discrepancias con la orden y con la preinscripción, declaradas y no
     corregidas en silencio**;
   - **lo que esto NO dice**.
6. **Commits por pieza**, para dar un SHA por entregable. Si separar dos piezas
   deja un estado intermedio con la suite en rojo, van juntas y se dice por qué.
7. Cerrar o avanzar las incidencias. Una incidencia `resuelta` lleva su hito con el SHA.
8. **Reporte al usuario en el formato que pidió**: SHA por pieza, veredicto por
   criterio, suite por entorno y lo que no se hizo.

## Reglas transversales, cada una con el incidente que la costó

- **Una compuerta que pasa en vacío es peor que ninguna.**
  - Un `.get("sound", True)` leía la clave donde no estaba, y dos compuertas de calidad
    pasaron sin mirar nada.
  - La plantilla de `pre-push` de esta misma skill decía «IDÉNTICO» sin correr nada
    hasta que se probó. Ahora una plantilla sin ajustar bloquea.
  - **Toda compuerta nueva se prueba con un caso que la haga fallar.**
- **Un sello bit a bit exige un entorno determinista.**
  - Con BLAS a 20 hilos, la 15.ª cifra cambiaba (0,15621506971410085 contra
    0,1562150697141007) y el reloj se triplicaba (411 s contra 119 s).
  - Fijar `OMP/OPENBLAS/MKL_NUM_THREADS=1` en un submódulo llega tarde si el
    `__init__` del paquete ya importó numpy. Se usa `threadpoolctl` al importar.
  - Antes de tocar una tolerancia, comprobar `threadpool_info()`.
- **Instalar el paquete de verdad al menos una vez.** El `build-backend` de
  `pyproject.toml` no existía y `pip install .` fallaba. Ninguna auditoría lo vio,
  porque todo se corría con `PYTHONPATH=src`. El CI habría muerto en el primer paso.
- **Un test tiene que pasar corrido solo.** Varios importaban el paquete sólo porque
  otro test había tocado `sys.path` antes. Se arregla con `pythonpath` en la
  configuración de pytest.
- **Ningún test lee fuera del repo**: los datos externos van versionados o el test se
  salta diciendo qué falta. Con trinquete por AST, y una lista **declarada** de
  excepciones de frontera. La regla nueva se cazó a sí misma dos veces al instalarla,
  y eso es buena señal.
- **Todo insumo externo se coteja al cargar**: sha esperado en el código y
  `AbortoDeCompuerta` si difiere. Que herede de `BaseException`, porque había 57
  `except Exception` en el código que se tragaban el aborto.
- **Una herramienta que sobrescribe evidencia commiteada** se restaura con
  `git checkout -- <fichero>` tras cada corrida, o se le cambia la salida.
- **Las rutas de un script se resuelven contra su carpeta.** Un comparador resolvía
  una ruta relativa contra la suya propia y decía «falta un artefacto». A esos
  scripts se les pasan rutas absolutas.
- **Un vigilante por `grep` se encuentra a sí mismo.** Usar `ps -C`, `kill -0` o
  `pgrep -x`, nunca `pgrep -f`.
- **El estado no vive en la prosa.** Un docstring dice el valor por defecto, no el
  estado actual. Antes de afirmar que algo está apagado o no existe: config,
  tablero, `git log`.
- **CI, hooks y lazo completo son tres capas distintas.**
  - El CI corre lo que cabe sin licencias: huellas, trinquetes y suite.
  - El `pre-commit` corre la suite rápida (~50 s).
  - El `pre-push` corre la referencia completa (~17 min en ATALANTA).
  - La regla escrita en `CONTRIBUTING.md`: **push sin hooks = sello no verificado =
    bug potencialmente publicado.**
- **El relevo entre sesiones ocurre por el disco, nunca por el chat.** Todo lo que
  una sesión nueva necesita saber está en la preinscripción, el resultado, el
  tablero o la memoria.

## Cómo se usa en un proyecto nuevo

1. Etapa 0: objetivo y entregable escritos, en la nota puerta o en el README.
2. Etapa 1: tabla de bloqueos con evidencia.
3. Etapa 2: una corrida de punta a punta, sellada, con su comparador y los tres
   casos que muerden.
4. Etapa 4: copiar `plantillas/AUDITORIA.md` a `docs/` y rellenarla sin tocar código.
5. Etapa 5: cada fase con `ariadna.py fase … sellar … cerrar`.
6. Instalar los hooks: copiar `plantillas/hooks/*` a `scripts/hooks/`, ajustar los
   marcadores `⟨…⟩` (hasta entonces el `pre-push` bloquea) y enlazarlos:
   `ln -s ../../scripts/hooks/pre-commit .git/hooks/pre-commit`.

## Lo que esta skill NO hace

- No decide el orden de las fases por ti: lo propone la auditoría y **decide el
  usuario**.
- No sustituye al tablero de incidencias (`wiki-de-proyecto`) ni a las reglas de
  cómputo caro (`corridas-largas-reproducibles`).
- No hace push ni publica nada.
