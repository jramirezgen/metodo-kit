---
name: code-principles
description: Enrutador de las 8 skills de principios de ingenieria de software (clean-architecture, domain-driven-design, separation-of-concerns[-pattern-overview], functional-immutability/functional-programmer, defense-in-depth, test-driven-development, refactoring-clean-code/code-refactoring-refactor-clean, pragmatic-programmer[-base]), que existen como skill de proyecto Y de cuenta con nombre distinto, mas autonomous-loop para trabajo largo multi-fase. Usar SIEMPRE al empezar un proyecto nuevo, diseñar una arquitectura o un modulo, escribir codigo/logica nueva, arreglar un bug, refactorizar, revisar codigo, emprender una feature que abarcara varias sesiones, o antes de declarar un diseño terminado o 10/10 (auditoria por principios + mapa de capas clasicas y transversales + revision adversarial independiente) — decide cuales cargar y en que orden, no solo si cargarlas.
---

# code-principles — orquestador de principios de ingeniería

Las 8 skills de principios de abajo **ya disparan solas** por su propia
`description` (cada una trae su "Cargar al..."). Este enrutador no las
reemplaza: resuelve el problema real, que es que una tarea normal necesita
**2–4 de ellas a la vez, en un orden concreto** — y confiar en que cada
trigger dispare por su cuenta deja huecos (se acuerda de TDD y se olvida de
defense-in-depth, por ejemplo). Una novena skill, `autonomous-loop`, no es un
principio de código — es la disciplina de fase para cuando la tarea completa
va a abarcar varias sesiones; ver su fila propia más abajo.

**Cómo se invocan:** las 8 de principios son skills habilitadas a nivel de
cuenta (vía MCPmarket), se cargan con la herramienta `Skill` pasando el
**nombre exacto de la tabla de abajo** — no hay ruta que leer ni archivo que
abrir, a diferencia de las skills de la biblioteca `/mnt/f/skills` (esas sí se
referencian por ruta vía el router `ingenieria-software`). `autonomous-loop`
se invoca igual, por nombre, aunque vive como skill de proyecto sintetizada en
`~/Documents/REPOSITORIOS/.claude/skills/autonomous-loop/` (no es nativa del
plugin ni tiene hook activo — ver su propio `SKILL.md` para el porqué).

⚠️ **Cuatro de las nueve existen DOS veces, con nombre distinto según el
ámbito. No hay un nombre "correcto": hay dos, y cuál funciona depende de la
sesión.** Medido contra el disco el 2026-09-18:

| rol | skill de **proyecto** (`~/Documents/REPOSITORIOS/.claude/skills/`) | skill de **cuenta** (la que lista `ListSkills`) |
|---|---|---|
| separación de responsabilidades | `separation-of-concerns` | `separation-of-concerns-pattern-overview` |
| programación funcional | `functional-immutability` | `functional-programmer` |
| refactor / code smells | `refactoring-clean-code` | `code-refactoring-refactor-clean` |
| meta-principios | `pragmatic-programmer-base` | `pragmatic-programmer` (global, en `~/.claude/skills/`) |

Las de proyecto son **síntesis propias** de los paquetes de
`/mnt/f/skills/Programacion y matematicas/`, creadas el 2026-09-05; su
`README.md` documenta el mapeo origen → nombre local (p. ej.
`code-refactoring-refactor-clean-1.0.0/` → `refactoring-clean-code/`). Las
otras cinco —`clean-architecture`, `domain-driven-design`,
`test-driven-development`, `defense-in-depth`, `autonomous-loop`— se llaman
**igual** en ambos ámbitos, y por eso nunca dieron problema.

> ⛔ **Este archivo ya se equivocó dos veces, en direcciones opuestas, y las dos
> por creer en una sola lista.** El 2026-09-06 declaró *inventados* los nombres
> cortos tras consultar `ListSkills` — que **sólo lista las skills de cuenta y
> no ve las de proyecto**; los cortos existían en disco desde el día anterior.
> El 2026-09-18, en `~/Documents/REPOSITORIOS`, pasó lo contrario: el hook de
> arranque reportó *«0 baseline skill(s) synced»*, los tres nombres **largos**
> fallaron y los **cortos** cargaron sin problema.
>
> **`ListSkills` es necesario pero NO suficiente.** Para saber qué existe de
> verdad hacen falta las tres fuentes: `ListSkills` (cuenta),
> `ls ~/Documents/REPOSITORIOS/.claude/skills/` (proyecto) y
> `ls ~/.claude/skills/` (global).

## Las 9 skills y su rol

| Skill (nombre exacto de invocación) | Rol | Cuándo |
|---|---|---|
| `pragmatic-programmer` **ó** `pragmatic-programmer-base` | Meta-principios: DRY, ortogonalidad, tracer bullets, reversibilidad, diseño por contrato | Casi siempre primero — decide si algo necesita abstracción antes de construirlo |
| `clean-architecture` | Regla de Dependencia, capas, puertos/adaptadores, SOLID | Estructura de un proyecto/módulo nuevo; lógica de negocio filtrándose al framework |
| `domain-driven-design` | Entidades vs value objects, agregados, bounded contexts, estados ilegales irrepresentables | Modelar un dominio, diseñar tipos/esquemas, nombrar conceptos de negocio |
| `separation-of-concerns` **ó** `separation-of-concerns-pattern-overview` | Componentes de responsabilidad única, orquestación separada de ejecución | Diseñar un handler/comando/endpoint nuevo; un test que necesita levantar DB/red para probar lógica |
| `test-driven-development` | Ciclo rojo-verde-refactor, "pruébalo" antes de tocar comportamiento existente | Antes de implementar lógica nueva o cambiar comportamiento existente; primer paso al arreglar un bug |
| `functional-immutability` **ó** `functional-programmer` | Principios de programación funcional (funciones puras, composición, mutar vs transformar) | Diseñar transformaciones de datos/pipelines; código con efectos secundarios ocultos |
| `defense-in-depth` | Validar en cada capa por la que pasa un dato | Arreglar un bug causado por dato inválido; decidir dónde poner una validación |
| `refactoring-clean-code` **ó** `code-refactoring-refactor-clean` | Catálogo de code smells, SOLID, priorizar deuda técnica | Código difícil de mantener, antes de un refactor grande |
| `autonomous-loop` | Fases (brainstorm→plan→work→review→fix→compound→test→ship), estado persistido, re-anclaje | Feature completa que abarcará varias sesiones o reinicios de contexto — no un cambio de una sentada |

**Duplicado conocido, no se invoca:** la cuenta también tiene habilitada
`principle-clean-architecture`, que cubre el mismo rol que `clean-architecture`
casi palabra por palabra (Dependency Rule, hexagonal, puertos/adaptadores).
Este enrutador siempre usa `clean-architecture` (nombre más corto, misma
cobertura) para no cargar dos veces la misma guía; si algún día una de las dos
cambia de contenido y dejan de solaparse, revisar esta nota.

## Si una invocación falla o no aparece en la sesión

**Ante un `Unknown skill`, el primer intento es SIEMPRE el otro nombre de su
fila.** No reescribas la tabla: las cuatro filas con `ó` llevan los dos nombres
porque los dos son reales, en ámbitos distintos. Fijar uno solo es exactamente
el error que este archivo ya cometió dos veces, en direcciones opuestas.

Si **ninguno de los dos** carga, entonces sí es una limitación de esta sesión
(pasó el 2026-09-06 en claude.ai con `test-driven-development` y
`defense-in-depth`, estando ambas habilitadas). No es arreglable desde aquí.
**No te quedes bloqueado ni lo declares imposible**: aplica la disciplina de la
skill de memoria —rojo-verde-refactor para TDD, validar en cada capa para
defense-in-depth; su rol está en la tabla de arriba— y **dilo explícitamente**
("cargando su disciplina sin la herramienta `Skill`, no disponible esta
sesión"), en vez de omitirla en silencio.

Y antes de reportar cualquier fallo de nombre, comprueba las **tres** fuentes
—`ListSkills` (cuenta), `ls ~/Documents/REPOSITORIOS/.claude/skills/`
(proyecto), `ls ~/.claude/skills/` (global)—, nunca una sola. `ListSkills` por
sí solo es lo que produjo el error de 2026-09-06.

## Combinaciones por situación (el orden importa)

| Situación | Invocar en este orden |
|---|---|
| **Proyecto nuevo** / definir estructura de carpetas | `pragmatic-programmer` → `clean-architecture` → `domain-driven-design` → `separation-of-concerns-pattern-overview` |
| **Módulo, tipo o endpoint nuevo** | `domain-driven-design` → `clean-architecture` → `separation-of-concerns-pattern-overview` |
| **Feature nueva** (lógica de negocio) | `test-driven-development` → `functional-programmer` (si transforma datos) → `defense-in-depth` (si el dato entra de fuera) |
| **Arreglar un bug** | `test-driven-development` (reproducir con test) → `defense-in-depth` (validar en la capa donde entró) |
| **Código difícil de mantener / pagar deuda técnica** | `code-refactoring-refactor-clean` → `pragmatic-programmer` |
| **Revisión de arquitectura o PR grande** | `clean-architecture` + `separation-of-concerns-pattern-overview` (estructura) → `code-refactoring-refactor-clean` (calidad) → `defense-in-depth` (validación) |
| **Feature grande, multi-sesión** (va a sobrevivir reinicios de contexto) | `autonomous-loop` primero, para fijar fases y estado — dentro de sus fases `work`/`fix` se invoca la fila que corresponda de esta misma tabla (feature nueva, arreglar bug, etc.) |
| **Declarar un diseño "terminado" o "10/10"** (antes de construir) | las dos lentes y la revisión adversarial de **"Un 10/10 se audita con dos lentes y un tercero"**, más abajo — nunca la autopuntuación sola |
| **Release de software** (versión nueva publicada, no un parche interno) | `clean-architecture` + `separation-of-concerns-pattern-overview` (auditar estructura/CLI) → `defense-in-depth` (validación en los bordes) → **ver "Todo release sustantivo demuestra su nivel de producción" abajo** |

## Todo release sustantivo demuestra su nivel de producción

> Añadida 2026-09-17 como "todo release va con su paper" (auditoría de AJOLOTE
> 2.3.1); **revertida 2026-09-27, decisión explícita del usuario**: «no quiero
> papers como tal — quiero que los prototipos alcancen el nivel para elevar a
> producción». El motivo de fondo no cambió (un CHANGELOG + bump de versión no
> le basta a quien decide si integrar la herramienta), pero el remedio sí: no
> se pide un documento narrativo tipo paper, se pide que el propio prototipo
> **llegue** al nivel que haría defendible subirlo a producción, y que quede
> **evidencia verificable** de que llegó — no un texto que lo cuente aparte.
> Este cambio ya estaba probado como excepción puntual en AJOLOTE desde el
> mismo día (ver `[[releases-van-con-su-paper]]`); aquí se vuelve la regla
> general, no la excepción.

**Qué dispara la regla.** Un release **sustantivo**: cambia arquitectura,
resultados de validación, o el alcance funcional de la herramienta. Un parche
mecánico (fix de packaging, bump de dependencia, typo) NO la dispara.

**Qué significa "nivel de producción" — se demuestra, no se narra:**
- **Arquitectura limpia**: capas, puntos de entrada (CLI/API) y las
  invariantes que garantiza — auditado con `clean-architecture` +
  `separation-of-concerns-pattern-overview`, no descrito en prosa aparte.
- **Suite de tests verde y con cobertura declarada** de lo que el release
  cambió, más los bordes validados con `defense-in-depth` — la prueba de que
  funciona es la suite corriendo, no un párrafo que lo afirme.
- **Resultados y validación reproducibles**: cada cifra que sostiene el
  release señala el script/comando exacto del repo que la produce (ruta +
  parámetros) y el baseline/gold-standard contra el que se comparó, con
  unidades y denominador explícitos — mismo criterio duro de siempre: cifras
  con fuente, nunca inventadas ni "≈" (ver
  `[[la-bandera-nunca-se-ensena-sola]]`). No hace falta que viva en un `.md`
  de tipo paper: basta con que el CHANGELOG o el README del release enlacen al
  script/notebook que la reproduce.
- **Deployable de verdad**: lo que hace falta para correrlo fuera de la
  máquina de quien lo escribió — dependencias fijadas, instalación
  documentada en dos líneas, sin credenciales ni rutas absolutas locales
  incrustadas.

**Sigue habiendo evidencia gráfica cuando el release la necesita** —una
figura que sustente una cifra de validación no desaparece—, pero se genera
**porque el análisis la necesita**, no porque el release exige un documento
con figuras. Cuando haga falta, usar igualmente la skill local
`scientific-visualization`
(`/mnt/f/skills/scientific-agent-skills/skills/scientific-visualization`,
referenciada, no copiada): paleta Okabe-Ito, `publication.mplstyle`,
exportación vectorial + raster vía `scripts/figure_export.py`.

**Cada release sí lleva un expediente técnico — profesional, no académico
(añadido 2026-09-27, misma decisión del usuario).** No haber pedido un paper
no significa no dejar nada escrito: la evidencia de arriba (arquitectura,
tests, reproducibilidad, deploy) se consolida en **un** documento por
release, con formato de **expediente técnico de ingeniería**, no de artículo
científico:

- **Qué lo distingue de un paper.** Sin abstract, sin sección de
  "trabajo relacionado", sin bibliografía, sin figuras Q1 por defecto, sin
  notebook Jupyter obligatorio. Es un documento de trabajo — el que un
  ingeniero de otro equipo leería para decidir si integra o despliega esta
  versión, no el que se somete a revisión por pares.
- **Qué secciones lleva, en orden:** alcance del release (qué cambió y qué
  no) · arquitectura y puntos de entrada · cómo se probó (suite, cobertura) ·
  resultados de validación contra baseline (cifra + script que la reproduce +
  denominador) · cómo desplegarlo · limitaciones y deuda conocida que queda
  abierta. Una tabla o una lista con viñetas basta; no hace falta prosa
  extensa por sección.
- **Dónde vive y cómo se nombra.** `docs/releases/EXPEDIENTE_<version>.md`,
  junto al CHANGELOG (que sigue siendo el índice corto). Se acumulan igual que
  antes se acumulaban los papers — nunca se pisa el de un release anterior.
- **De dónde sale.** No se redacta a mano libre: reusa exactamente lo que las
  skills de arriba (`clean-architecture`, `separation-of-concerns-pattern-overview`,
  `defense-in-depth`) ya auditaron y lo que la suite de tests ya corrió — el
  expediente compila esa evidencia, no la vuelve a producir en prosa.

**Dónde vive la evidencia.** El CHANGELOG sigue siendo el registro corto por
versión; el expediente técnico es el documento largo hermano — pero de
ingeniería, no un paper — y el propio repo (tests, CI, scripts reproducibles)
sigue siendo la fuente que el expediente sólo referencia, nunca sustituye.

Si la tarea no encaja limpio en una fila, usa el default: `pragmatic-programmer`
primero (siempre), y de ahí las que la tabla de roles indique por keyword de la
tarea (dominio → DDD, entrada externa → defense-in-depth, transformación →
`functional-programmer`, mantenibilidad → `code-refactoring-refactor-clean`).

## Un 10/10 se audita con dos lentes y un tercero

> Añadida 2026-10-03 (AQUERONTE), a pedido explícito del usuario: *«agrega esos
> detalles de capas y las revisiones que haces, para que los siguientes
> proyectos sean mejores»*. Nace de un fallo medido: la arquitectura de
> AQUERONTE se autopuntuó **10/10** frente a los siete principios de
> `pragmatic-programmer`, y una sola pregunta del usuario («¿hay capa de
> presentación, lógica, datos, integración, transversales?») encontró **siete
> huecos**. La nota honesta frente a ese mapa era **8/10**. El criterio que
> se mide decide lo que se ve, y lo que no se mide se da por bueno sin querer.

**Regla.** Un diseño no se declara 10/10 hasta pasar **tres** comprobaciones, en
este orden. Cada nota sale con la **lista de brechas** que la separa del 10 (la
regla de puntuación de `pragmatic-programmer`); una nota sin esa lista no vale.

### Lente 1 · Principios

DRY, ortogonalidad, bala trazadora, contratos, ventanas rotas, reversibilidad y
estimación: la tabla de diagnóstico de `pragmatic-programmer`. Responde a *«¿el
diseño está bien razonado?»*. **No** responde a *«¿tiene todas sus piezas?»*.

### Lente 2 · Mapa clásico de capas, cada fila con sitio + regla de imports + test

| Capa | Pregunta que se hace al diseño | Hueco típico (visto en AQUERONTE) |
|---|---|---|
| **Presentación** | ¿Formatear la salida está separado de orquestar? | la CLI hacía las dos cosas; faltaban presentadores (JSON, tabla, Markdown) |
| **API pública** | ¿Hay una fachada programática estable, y la CLI es un cliente más de ella? ¿Un test congela sus firmas? | solo había CLI; otros repos o notebooks no tenían por dónde entrar |
| **Aplicación** | ¿Los casos de uso y el **orquestador del pipeline** tienen capa propia? | el DAG de artefactos no tenía hogar y acababa en un adaptador |
| **Dominio** | ¿Es puro: sin I/O, reloj, aleatoriedad global ni configuración? | — (suele estar bien si se aplicó `clean-architecture`) |
| **Datos / persistencia** | ¿Los artefactos llevan **versión de esquema** y serialización canónica? ¿Un lector viejo rechaza un esquema futuro? | faltaba la versión de esquema |
| **Integración** | ¿Cada sistema externo pasa por un adaptador con anticorrupción, pin verificado y contract test? ¿Hay **política de red** (caché, sha256, timeout, reintento, modo sin red)? | faltaba la política de red, con dos servidores públicos caídos ese mismo día |
| **Transversales** | Ver las siete filas de abajo | estaban dispersas |

**Las siete transversales, cada una con su sitio y su compuerta:**

1. **Configuración**: un único objeto inmutable, validado **una vez** en la raíz de composición. Trinquete contra `os.environ`/`getenv` fuera de ese módulo; una clave desconocida aborta.
2. **Errores**: una excepción raíz del proyecto, excepciones con nombre y una tabla estable de códigos de salida. Trinquete contra `except Exception` silencioso.
3. **Observabilidad**: log estructurado (JSON lines) y **coste medido por etapa** (tiempo, CPU, memoria pico) escrito al manifiesto. Así las estimaciones PERT salen de datos y no de cronómetro a mano.
4. **Reproducibilidad**: semilla y reloj entran como puertos; BLAS a un hilo **forzado** en la composición (no solo comprobado); el entorno (versiones, pins, CPU) se captura en el manifiesto.
5. **Seguridad / secretos**: siempre por ruta, nunca por valor ni en git; trinquete antisecretos en `pre-commit` y en la CI; el manifiesto registra *que* se usó una credencial, nunca su valor.
6. **Concurrencia**: candado de máquina para corridas pesadas y detección de las de otros repos con `pgrep -x` (no `grep`, que se encuentra a sí mismo).
7. **Empaquetado / despliegue**: lockfile versionado, semver, CHANGELOG e instalación en dos líneas **probada en un clon limpio por la CI**.

**La regla que las mantiene limpias:** el dominio **nunca** importa lo
transversal. Le llega solo por puertos (`Bitacora`, `Medidor`, `Semilla`,
`Reloj`) o como un valor ya validado que la raíz de composición pasa hacia dentro.

**Lo que se decide NO poner también se escribe**, con su porqué y cómo se
revertiría. Ejemplos: servidor HTTP y base de datos sin consumidor real. Cada
uno entraría luego como un adaptador más, sin tocar el dominio. Un hueco
declarado es una decisión; uno callado es un defecto.

### Tercero · Revisión adversarial independiente

La autopuntuación **no es evidencia**: los huecos que quedan son los que quien
diseñó no está mirando. Antes de declarar el 10 se lanza un agente
independiente (`Agent`, en segundo plano) con estas condiciones:

- **Solo lectura** y **un único encargo: romper el diseño.** Sin escribir código.
- Lee **solo los artefactos del diseño** (arquitectura, plan, DAG), **no el chat**. Así no hereda los supuestos de quien diseñó.
- Recibe la lista de **decisiones cerradas del usuario y reglas del entorno que no puede discutir**. Puede señalar sus consecuencias, pero no proponer quitarlas.
- Ataca en este orden:
  - **A** contaminación o fuga entre lo que construye y lo que valida;
  - **B** contradicciones entre documentos y DAG (dependencias, estados, orden imposible);
  - **C** huecos de capas;
  - **D** huecos del dominio (en ciencia: numéricos, y si los criterios de éxito pueden cumplirse de forma trivial);
  - **E** mecanismos que son solo prosa, sin test ni hook que los fuerce;
  - **F** sobreingeniería que retrasa la primera evidencia.
- **Formato exigido**: severidad (BLOQUEANTE, ALTA, MEDIA o BAJA), sitio exacto, escenario concreto de fallo, arreglo mínimo y su nota de 0 a 10. Debe verificar cada afirmación contra el texto, sin relleno.

Mientras corre, **no se tocan los archivos que revisa**, para que revise una
versión fija. Al volver, cada hallazgo se **verifica contra el texto** antes de
aceptarlo: un revisor también puede inventar. Lo aceptado entra al tablero de
incidencias y al DAG.

**Desenlace medido en AQUERONTE (2026-10-03).** Tras pasar las lentes 1 y 2, la
autoevaluación volvió a dar 10. La revisión adversarial dio **5/10**, con 18
hallazgos y 4 bloqueantes, y **los 18 eran ciertos**. Los cierres los escribe el
mismo autor que los defectos, así que el 10 exige una **segunda ronda** sobre la
versión cerrada.

**Antes de diseñar o puntuar, abre
[references/lecciones-de-arquitectura.md](references/lecciones-de-arquitectura.md).**
Reúne los fallos que se repiten y el mecanismo que cierra cada uno:
- tabla de roles juez/entrada y el agente como canal de fuga;
- preinscripción como ancestro git;
- particiones de desarrollo y confirmación;
- bandas de sensibilidad;
- plan como datos con reglas que se niegan a generar;
- pins alcanzables y `jueces_vistos` heredados;
- CI con historial completo;
- colisiones de nombres;
- el contador de nodos hasta la primera evidencia.

Úsalo también como **guion de ataque** para el revisor: pásale los títulos de
las secciones A–G.

### Y aun así, el 10 de diseño no es el ¡EUREKA!

Tras las tres comprobaciones, el diseño es 10/10 **en el papel**. Se declara
¡EUREKA! cuando la **bala trazadora** atraviesa todas las capas de punta a
punta y los tests de arquitectura (contratos de imports, trinquetes, firmas
de la API) impiden romperlas. Hasta entonces, la respuesta honesta a *«¿ya
está al 10?»* es *«en el papel, sí; demostrado, todavía no»*.

## No genera contenido propio

Este archivo no repite las reglas de cada skill — eso ya vive en su propio
`SKILL.md` y se cargaría dos veces. Si una fila de arriba queda desactualizada
porque una de las 8 cambió de nombre o descripción, corrígela aquí
contrastando con `ListSkills` (no con lo que "debería" llamarse); no dupliques
su contenido.

## Relación con `ingenieria-software`

`ingenieria-software` (el otro enrutador ya instalado) cubre patrones
específicos de stack — Docker, Postgres, diseño de APIs REST, git, CI. Este
skill cubre los **principios transversales de diseño de código**, agnósticos
al stack. Para una tarea concreta suelen combinarse: p.ej. "diseñar una API
REST nueva" → `api-design` (de `ingenieria-software`) para la forma del
contrato HTTP, y `clean-architecture` + `separation-of-concerns-pattern-overview`
(de aquí) para que el handler no contenga la lógica de negocio.
