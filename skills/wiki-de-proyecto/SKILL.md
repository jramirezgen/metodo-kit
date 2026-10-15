---
name: wiki-de-proyecto
description: "Convierte un repo en wiki repo: su documentación viva pasa a la carpeta del proyecto dentro de la bóveda de Obsidian, donde se lee y se edita a mano, mientras el repo guarda la intención —los generadores y wiki.json— con las garantías de git. Publica mapas en JSON Canvas (.canvas), bases nativas de Obsidian (.base), el tablero de incidencias y el histórico de diseños. Úsala cuando haya que ver un pipeline o una arquitectura entera de un vistazo, cuando se pida un canvas, un flujograma, un tablero de incidencias o una base de Obsidian, cuando haya que ampliar o corregir algo ya publicado, y cuando un repo nuevo estrene su wiki. Reglas duras: nada se edita a mano donde se genera; publicar se niega a pisar una edición manual no adoptada; ningún diseño anterior se pierde y publicar corre los generadores declarados, así que una nota nueva se indexa en la misma operación; y no se publica un canvas sin pasar la compuerta de legibilidad. Contra el desvío: `## Marco` en la nota puerta, criterio satisfacible antes de correr, y con 2 intentos fallidos se re-ancla con auditoría conceptual. Los repos se hablan por incidencias. Comando de entrada: scripts/iniciar.py."
license: MIT
metadata:
  version: "2.7.0"
  autor: "Kaitokid"
  creado: "2026-09-08"
  actualizado: "2026-10-12"
---

# wiki-de-proyecto — la documentación viva es un repo, y vive en la bóveda

Se llamaba `canvas-de-proyecto` y cubría la mitad: un canvas. Dejó de ser cierto
en cuanto entró la primera `.base`. Lo que esta skill instala no es un dibujo —
es **un repo de documentación con las garantías de git, cuyo árbol de trabajo
está dentro de Obsidian**.

## El comando

```bash
S=/mnt/f/skills/_personales/wiki-de-proyecto/scripts

python3 $S/iniciar.py <repo> --proyecto NOMBRE            # ensayo: dice qué haría
python3 $S/iniciar.py <repo> --proyecto NOMBRE --aplicar  # estrena el wiki repo
python3 $S/iniciar.py <repo> --aplicar                    # lo pone al día
```

**Decide por lo que encuentra, no por una bandera.** Si no hay `wiki.json`,
*estrena*: crea `docs/wiki/`, copia las piezas, siembra el manifiesto y la
plantilla, prepara las carpetas de la bóveda y la nota puerta. Si ya lo hay,
*pone al día*: re-copia **sólo** lo vendorizado y no toca ni el manifiesto ni
los generadores del proyecto — por eso es seguro correrlo las veces que haga
falta, que es la única forma de que alguien lo corra.

`--mapas-de X` es para cuando los mapas son de **una pieza** del repo y no del
repo entero (ELEMENT publica los mapas de APOLO). Si no, se omite.

## La arquitectura, en una tabla

Un wiki repo tiene **dos mitades y ninguna sobra**. Obsidian no abre un fichero
que vive en el sistema de ficheros de WSL, y un fichero de la bóveda no tiene
historia; juntos, sí.

    <repo>/docs/wiki/            ──genera──▶   <vault>/wiki/<PROYECTO>/
    la INTENCIÓN                              el ÁRBOL DE TRABAJO
    (versionada en git)                       (donde se lee y se edita a mano)

| git | aquí | quién lo escribe |
|---|---|---|
| working tree | `wiki/<PROYECTO>/` en la bóveda | **el humano**, a mano, en Obsidian |
| índice + HEAD | `wiki.json` (qué debería haber) + los generadores | el humano, en el repo |
| `git status` | `situacion()` de `wiki_repo_lib.py` | generado |
| `git add` | `publicar.py --adoptar` | — |
| `git checkout` | `publicar.py`, que **se niega a pisar** lo no adoptado | — |
| `.git/index` | `wiki.lock.json` — lo **observado** | generado, nunca a mano |

`wiki.lock.json` guarda, por artefacto, **dos** huellas: la canónica del repo y
la de la bóveda tal y como quedaron la última vez. Hacen falta las dos —igual
que el índice de git recuerda el blob *y* el árbol— o adoptar una edición manual
la dejaría pisable en la corrida siguiente.

### La estructura dentro de la bóveda

```
wiki/<PROYECTO>/
├── <PROYECTO>.md              ← la NOTA PUERTA. La escribe un humano.
│                                Sin ella `publicar.py` se niega a publicar.
├── <TITULAR>/Mapas/           ← los .canvas numerados + su índice `00 — Mapas de X`
│   └── Versiones/             ← el histórico: cada diseño que se archivó
├── Bases/                     ← los .base numerados (bases nativas de Obsidian)
└── Incidencias/               ← el tablero: una nota por incidencia
```

**Numeración densa y siempre**: `01 — …`, `02 — …`. Un mapa sin número no tiene
orden de lectura, y una carpeta sin orden de lectura se lee al azar.

### Cuando el proyecto tiene VARIOS titulares (2026-09-09)

`--mapas-de` nació para un proyecto con **un** titular: ELEMENT publica los mapas
de APOLO, deja `Bases/` en la raíz y comprueba `ELEMENT.md` como puerta. SAPYRIA
tiene **tres** —SMALLRNA, WES y WGS, un repo cada uno— y ahí esas tres decisiones
se rompen a la vez:

| pieza | con un titular | con varios |
|---|---|---|
| `bases`, `incidencias` | pueden colgar del proyecto | **cuelgan del titular**, o dos repos que no se conocen escriben `01 — …` en la misma carpeta |
| titular del tablero | es el proyecto | es el titular: cada repo lleva su propia serie `INC-###` |
| nota puerta comprobada | `<PROYECTO>.md` | `<TITULAR>/<TITULAR>.md`, o la corporativa acaba siendo un índice técnico que crece con cada pipeline |

Los tres se resuelven **por el manifiesto**, no por una bandera ni por código:

```json
"estructura": {
  "mapas": "SMALLRNA/Mapas",
  "mapas_de": "SMALLRNA",
  "incidencias_de": "SMALLRNA",
  "versiones": "SMALLRNA/Mapas/Versiones",
  "bases": "SMALLRNA/Bases",
  "incidencias": "SMALLRNA/Incidencias"
}
```

`incidencias_de` es nuevo y **por defecto es el proyecto**, así que ELEMENT no
declara nada y no cambia. La puerta la decide el disco: `publicar.py` usa
`<TITULAR>/<TITULAR>.md` **si esa nota existe** y si no la del proyecto — APOLO
no tiene `APOLO.md`, así que ELEMENT sigue comprobando la suya.

> ⛔ **Lo que costó el error.** SMALLRNA, WES y WGS se estrenaron como
> `wiki/SMALLRNA/`, hermanos de `wiki/SAPYRIA/`, y su nota puerta decía que «la
> vista lógica basta, aunque en disco sean carpetas hermanas». No basta: quien
> abrió la carpeta corporativa buscando el canvas de un pipeline no encontró
> ninguno, y esa es exactamente la pregunta que un mapa existe para contestar.
> **Una jerarquía que sólo vive en los enlaces no es una jerarquía.**

### Las piezas, y cuáles se copian

| pieza | qué hace | ¿vendorizada? |
|---|---|---|
| `canvas_lib.py` | construir, disponer y **medir** un JSON Canvas | ✅ |
| `base_lib.py` | construir un `.base` de Obsidian y validarlo contra el disco | ✅ |
| `wiki_repo_lib.py` | huellas, `situacion()`, adopción | ✅ |
| `publicar.py` | publicar con sus compuertas | ✅ |
| `archivar.py` | guardar el diseño vigente **antes** de pisarlo | ✅ |
| `generar_incidencias.py` | el tablero de incidencias y su Base | ✅ |
| `generar_versiones.py` | el histórico de diseños y su Base | ✅ |
| `generar_<lo tuyo>.py` | **tu** mapa | ❌ nunca: sabe de qué proyecto es |

> **Se vendoriza lo que no tiene política.** Lo específico del proyecto vive en
> `wiki.json`, jamás dentro del código copiado. Ésa no es una preferencia de
> estilo: `publicar.py` llegó a divergir **163 líneas** de su original porque
> tenía `tema: [Motor ELEMENT]` escrito dentro, así que no se podía copiar sin
> editarlo — y editar una copia es exactamente cómo nace una divergencia.

Se **copia** y no se enlaza: el repo debe seguir siendo autónomo aunque `/mnt/f`
no esté montado. Por eso todo es **stdlib pura**.

⚠️ **Y la copia necesita una compuerta que la corra.** El comprobador
(`scripts/tests/test_vendorizado.py`) existía y aun así `publicar.py` divergió
otra vez **el mismo día en que se arregló**: el test vivía en la skill, y la
skill no la corre nadie. La compuerta de verdad va en la suite del repo
consumidor — patrón en
`element/tests/test_lo_vendorizado_no_ha_divergido_de_su_skill.py`.

## Las reglas duras

> **0. El tablero de incidencias es la PUERTA. Un canvas no se toca sin pasar
> por él.**
> Los mapas son el corazón de la wiki operativa, y lo que un mapa dibuja son
> decisiones y deudas — que viven en `Incidencias/`, no en la cabeza de quien
> dibuja. Así que el orden es siempre el mismo, y no tiene atajo:
>
> 1. **leer** `00 — Incidencias de <TITULAR>.md` antes de proponer nada;
> 2. **escribir o actualizar** la incidencia que sostiene el cambio, anclada
>    con `mapa_n` y `nodo`;
> 3. **regenerar** el mapa, ya con esa incidencia dentro;
> 4. **publicar**, que reindexa en la misma operación.
>
> Saltarse el paso 1 produce trabajo que no le consta a nadie; saltarse el 2
> produce un mapa que dibuja algo que ninguna nota sostiene. Y un hallazgo
> medido contra el repo **entra al tablero antes que al lienzo**: el lienzo es
> derivado, la incidencia es la fuente.
>
> ⛔ **Corolario que costó una corrección (2026-09-10): `la #N` nombra un
> DOCUMENTO de la serie numerada, no una casilla.** El tablero tiene dos cosas
> numeradas a la vez —los ficheros `NN.<título>` de la serie de RFC, y las
> casillas `- [ ]` del cuerpo de cada nota—, y en una frase hablada suenan
> igual. Ante *«toca la #3»*, la lectura por defecto es **el documento `03.`**;
> si de verdad se hablaba de una casilla, se pregunta o se hacen las dos, pero
> no se elige la interpretación estrecha en silencio.

> **0·bis. El objetivo se fija antes de tocar nada — general, y uno específico
> por rama si la hay.**
> Añadida 2026-09-17, a pedido explícito del usuario. La causa medida de dar
> vueltas sin cerrar nada es siempre la misma: el objetivo se asume y nunca se
> escribe, así que dos sesiones después nadie recuerda cuál era y el trabajo
> se va por la rama — literalmente, cuando el proyecto tiene varios titulares
> o sub-proyectos (regla 0 de la arquitectura, más arriba). Al invocar esta
> skill sobre un proyecto:
>
> 1. **El objetivo general se declara, no se asume.** Si no está escrito en la
>    nota puerta, se **pregunta** al usuario o, si el contexto ya lo deja
>    claro (el tablero de incidencias, la conversación en curso), se **infiere
>    y se declara** antes de seguir — mismo principio que la regla de
>    autoridad epistémica del vault: lo que no se declara, se olvida.
> 2. **Cada rama lleva su objetivo específico**, y ese objetivo vive siempre en
>    uno de dos estados: **resuelto** o **pausado**. Nunca "olvidado" — una
>    rama sin estado explícito es exactamente el fallo que esta regla cierra.
>    No hace falta maquinaria nueva para esto: basta un encabezado `## Objetivo`
>    en la nota puerta del proyecto o del titular (la misma nota que la regla
>    de arquitectura ya exige), con una línea por rama y su estado.
> 3. **Al cumplirse un objetivo — con los criterios de calidad que le
>    correspondan, apoyándose en las skills que hagan falta** (`code-review`,
>    `test-driven-development`, `pragmatic-programmer`, lo que el trabajo
>    pida) **— se declara ¡EUREKA!**: un cierre explícito y nombrado, no un
>    "ya quedó" implícito que nadie vuelve a mencionar. No es un ritual forzado
>    en cada tarea pequeña: depende del objetivo — se grita cuando el objetivo
>    general o el de una rama efectivamente se cumplió, y se omite cuando la
>    tarea no tenía uno declarado que cerrar.
> 4. **Nunca se bloquea un objetivo por extraño, tosco o mal planteado que
>    parezca.** Prohibido devolver una falsación fuerte — «esto no se puede,
>    punto» — como respuesta final y quedarse ahí. Se declara la dificultad
>    concreta y se **propone siempre una alternativa** que logre el objetivo
>    completo o, si entero no es posible, la parte que sí lo es. Bloquear sin
>    alternativa es el mismo error que dar vueltas sin objetivo: en los dos
>    casos el trabajo se detiene y nadie cierra nada.

> **0·ter. Contra el desvío: el marco fundacional se escribe, cada nodo se
> ancla a él, y dos intentos fallidos obligan a re-anclarse antes del tercero.**
> Añadida 2026-10-12, a pedido explícito del usuario: *«incorpora alguna
> estrategia adicional para dichos desvíos, porque ya muchas veces ha pasado
> y hemos perdido tiempo, recursos y tokens»*.
>
> **El caso que la motivó.** S.04 de AQUERONTE se lanzó ocho veces, unas
> 30 h de máquina, buscando valles con un criterio que **ningún estado podía
> cumplir**: la cara incluía complejos ES de transportadores sin sustrato,
> contra la decisión D-166. Además faltaban los ingredientes que el marco
> fundacional exigía: los sensores de flujo de Heinemann y Kochanowski y la
> prueba estructural de Feinberg y Thomas **antes** de buscar. Todas las
> revisiones adversariales, que eran de código (8,5/10), pasaron. Una sola
> auditoría **conceptual** lo encontró en 11 minutos. El objetivo seguía
> escrito (0·bis); lo que se perdió fue el **cómo** que se había acordado al
> principio.
>
> 0·bis fija el **qué**. 0·ter protege el **cómo**:
>
> 1. **`## Marco` en la nota puerta, escrito el primer día.** Contiene:
>    - la teoría o el enfoque elegido;
>    - las herramientas que deciden **antes** de gastar (pruebas
>      estructurales, casos conocidos, juez);
>    - el orden acordado;
>    - los ingredientes sin los cuales el objetivo no puede salir.
>
>    Se copia de lo que se acordó con el usuario, no se resume de memoria. Se
>    cambia solo con su firma, y el cambio se archiva igual que un diseño. Si
>    falta la sección, `publicar.py` avisa.
> 2. **Cada «hacer X antes de Y» del marco es una arista del DAG**, no prosa.
>    Si la prueba previa existe solo en un párrafo, nadie la exige y el nodo
>    caro se lanza sin ella (ver la skill `dag-de-proyecto`).
> 3. **Antes de una corrida cara, el criterio debe ser satisfacible.** Se
>    prueba en un caso trivial o conocido: un test de juguete que lo cumpla y
>    otro que no, y el punto de partida evaluado contra el criterio. Si el
>    propio punto de partida lo incumple por construcción, no se corre: se
>    revisa el criterio. En S.04, x̄ ya lo incumplía antes de buscar.
> 4. **Disparador de re-anclaje, mecánico.** La incidencia de un nodo lleva
>    `intentos: N` (intentos fallidos o corridas que superaron 2× lo
>    estimado). Con N ≥ 2, antes del siguiente intento:
>    - se re-lee `## Marco` y se contesta en la incidencia **qué pedía el
>      marco antes de este nodo** y si se hizo;
>    - se comprueba si el criterio contradice alguna decisión vigente
>      anterior;
>    - se lanza una **auditoría conceptual independiente** (punto 5);
>    - se escribe `reanclaje: <fecha> <desenlace>` en el frontmatter.
>
>    `publicar.py` avisa de toda incidencia abierta con `intentos ≥ 2` sin
>    `reanclaje:`. Es un aviso y no un fallo, para que no se ignore.
> 5. **Auditoría conceptual ≠ revisión de código.** Una revisión de código
>    pregunta si el diff hace lo que dice. La conceptual, en cambio, pregunta
>    si lo que se mide responde a la pregunta del marco:
>    - si el criterio es alcanzable;
>    - si está el mecanismo que el marco exige;
>    - si la escala y el medio son los acordados.
>
>    El agente es de solo lectura y lee el marco, las decisiones y los datos
>    de la corrida, no el chat. Corre con el disparador y en cada cierre de
>    hito. Las dos auditorías hacen falta, y ninguna sustituye a la otra.
> 6. **El desvío se contabiliza.** Cuando se detecta, se abre una incidencia
>    `tipo: desvio` con lo que costó (intentos, horas de máquina) y qué parte
>    del marco se había perdido. Es la única forma de saber si esta regla
>    funciona.

> **1. Donde se genera, no se edita a mano.**
> La fuente es `docs/wiki/generar_*.py`; el `.canvas` y el `.base` son
> artefactos. Un mapa mantenido a mano se desincroniza, y un mapa
> desincronizado es peor que ninguno porque se sigue creyendo.

> **2. Pero en la bóveda sí se edita — y publicar se niega a pisarlo.**
> Es la mitad que hace que esto sea un repo y no un exportador. Se edita a
> mano, `situacion()` lo ve como `git status`, y o se **adopta**
> (`publicar.py --adoptar`) o el siguiente publicado se niega a sobrescribirlo.
> Un artefacto puede además declararse `procedencia: manual` en `wiki.json`:
> entonces el sistema sólo lo numera, le pone ficha y lo indexa.

> **3. Ningún diseño anterior se pierde.**
> Antes de pisar un mapa, `archivar.py` copia el vigente a `Versiones/` como
> `NN — <título> (vN, AAAA-MM-DD).canvas` **con su nota**, que transcluye el
> lienzo y dice qué nodos nacieron, murieron o cambiaron de texto. Nunca borra:
> sólo añade. Es lo que pidió el usuario por su nombre —*«como es git, se
> tendrá que archivar de manera de nunca perder los diseños anteriores»*— y sin
> ello la única historia era el git del repo, que no se abre desde Obsidian.

> **3·bis. Publicar corre los generadores que el manifiesto declara: una nota
> nueva se indexa en la misma operación.**
> Una Base es una **consulta** y no deja ningún enlace en el fichero, así que la
> única arista del grafo hacia esas notas es la lista de `[[enlaces]]` de su
> índice. Ese índice lo escribe el generador que `wiki.json` declara — y
> `publicar.py` sólo lo **nombraba**: copiaba el `.base` y, si faltaba,
> preguntaba «¿corriste su generador?». Mordió dos veces seguidas: la v2 de un
> lazo de control se archivó bien y **nació sin índice**, y al día siguiente una
> incidencia escrita a mano en Obsidian se publicó y salió como **no indexada**
> en la auditoría del vault. Hoy publicar corre **todos** los generadores
> declarados, antes del bucle de Bases porque un índice transcluye la Base que
> ese bucle publica. Un `generador` declarado que no existe **es un fallo**: el
> manifiesto estaría prometiendo un índice que nadie puede escribir. Y un
> proyecto que archiva **declara su Base del histórico o no publica**, con el
> bloque JSON exacto dictado por el generador.

> **4. Ninguna cifra se teclea de memoria, y los huecos se dibujan igual de
> grandes que lo que funciona.**
> Cada número de un nodo sale del repo o de una corrida nombrada. Si depende de
> un dato que aún no existe, se dibuja **nombrando el dato que falta**. Un mapa
> que sólo enseña las flechas verdes miente sobre el estado del sistema.

> **5. Un reporte extenso que ya funciona bien se eleva ENTERO a Alejandría —
> por una regla declarada, nunca por un juicio de la IA caso a caso.**
> Añadida 2026-09-13, a pedido explícito del usuario: hasta ahora era la propia
> IA quien decidía, conversación a conversación, si un informe largo merecía
> vivir en Alejandría — y esa decisión repetida gasta tokens que una regla fija
> no gasta. La regla:
>
> - **Qué se eleva.** El reporte técnico completo de una fase/protocolo del
>   repo cuando esa fase ya cerró con su propio gate en PASS (o equivalente:
>   `checkpoint` verde, incidencia cerrada, versión aceptada) — no un borrador,
>   no un intento fallido. Ejemplo en un pipeline clínico: `technical_report.md`,
>   `*_qc_report.json` ya en PASS, el informe final de una corrida nombrada.
> - **Esto no es pedir escribir un paper (ajustado 2026-09-27, decisión
>   explícita del usuario).** Esta regla eleva un reporte que **ya existe**
>   porque el repo lo produjo al cerrar un gate — no instruye a redactar un
>   documento narrativo académico por cada release, ver
>   `[[releases-van-con-su-paper]]`. La prioridad del trabajo de un prototipo
>   sigue siendo alcanzar el nivel que lo haga defendible para producción
>   (tests, reproducibilidad, deploy); el reporte elevado es evidencia de eso,
>   no el objetivo en sí. Cuando ese reporte es el expediente técnico
>   profesional del release (`EXPEDIENTE_<version>.md`), aplica la misma
>   regla: se eleva entero si el gate cerró en PASS, igual que cualquier otro
>   reporte técnico cerrado.
> - **Qué NO se eleva — eso sigue siendo `wiki/` y solo `wiki/`.** Issues
>   (`Incidencias/`), canvas/mapas, conceptos, y las definiciones vivas de
>   protocolo o de esquema de base de datos: son información **rápida**, que
>   cambia con el proyecto, y Alejandría existe para lo que ya se congeló.
>   Meter ahí lo que todavía se edita a diario es contaminar la biblioteca con
>   lo que la wiki ya resuelve mejor.
> - **Excepción declarada — protocolos y bases de datos SÍ se identifican en
>   Alejandría, sin duplicarse.** Su versión autoritativa sigue viviendo en
>   `wiki/` (regla de esta misma skill: ahí se edita a mano). Pero además
>   reciben una **ficha puntero** en Alejandría — `al:` + `resumen:` mínimos y
>   `fuente:` apuntando de vuelta a la nota de `wiki/`, sin transcluir ni
>   copiar el contenido — para que aparezcan en el catálogo de quien busca por
>   Alejandría y no sepa que el dato vive en la wiki.
> - **Dónde, y por qué no como hasta ahora.** El vault ya tiene el error que
>   esta regla evita: `AGROGLIM`, `AGROGLIM_HAMCAO`, `AGROGLIM_VINAZA`,
>   `SHEWANELLA`, `SHEWANELLA_MODELO`, `SHEWANELLA_OMICAS`,
>   `SHEWANELLA_RUTAS`, `BIOMINED`, `BIOMINED_ACIDITHIOBACILLUS` son
>   colecciones **hermanas y planas** que en realidad son un proyecto y sus
>   ramas/sub-proyectos — una jerarquía que solo existe en el sufijo del
>   nombre, no en el disco (el mismo error de fondo que la regla 0 de
>   `wiki_repo_lib` ya nombró para `wiki/SMALLRNA` como hermana de
>   `wiki/SAPYRIA` en vez de anidada bajo ella). De aquí en adelante, un reporte
>   elevado va en una carpeta **anidada de verdad**, calcada de la jerarquía
>   real del proyecto — titular → rama/sub-proyecto → corrida, tantos niveles
>   como el proyecto tenga —, nunca en una colección plana con guion bajo:
>   `alejandria/<TITULAR_RAIZ>/<rama_o_subproyecto>/.../AL-####_slug.md`. El
>   `AL-####` sigue siendo un ID global plano (eso ya funciona bien, no se
>   toca); lo que cambia es la carpeta que lo contiene y el valor de
>   `coleccion:` en su frontmatter, que se escribe con la misma ruta anidada
>   (p. ej. `SAPYRIA/WGS/HG001-pilot-01`) para que el catálogo agrupe por rama
>   real y no por un sufijo de nombre.
> - **Se declara en `wiki.json`, no se improvisa.** Mismo patrón que
>   `estructura`/`mapas_de`: un bloque `alejandria` en el manifiesto fija
>   `coleccion_raiz` (la ruta anidada de este repo) y qué patrón de salida
>   cuenta como "reporte que ya funciona bien". Ver ejemplo en
>   `docs/wiki/wiki.json` de `wgs-clinical-pipeline` (primer repo que adopta
>   esta regla, 2026-09-13).
> - **Alcance de esta regla: hacia adelante, no retroactivo.** Aplica a partir
>   de esta edición de la skill, empezando por los wiki repos que la usen desde
>   ahora. Reordenar lo que YA está disperso en Alejandría (los pares
>   proyecto/rama listados arriba) y catalogar los huérfanos existentes es un
>   trabajo aparte, deliberadamente **no** incluido aquí — hacerlo todo de una
>   vez gastaría tokens que el usuario pidió explícitamente no gastar todavía.
>   Queda anotado como pendiente, no como resuelto.
> - **Lo que esta regla NO instala todavía.** Un script que lea el bloque
>   `alejandria` de `wiki.json` y eleve automáticamente al publicar —hoy la
>   regla es una convención declarada y aplicada a mano, no una compuerta
>   mecánica en `publicar.py`—. Automatizarlo es el siguiente paso natural,
>   no el de hoy.

> **6. Cerrar una incidencia commitea sola — sólo el commit, nada más.**
> Añadida 2026-09-13. `publicar.py` compara, para cada incidencia de
> `Incidencias/`, la `situacion:` de hoy contra la que `wiki.lock.json`
> observó la última vez que se publicó. Si una incidencia **acaba de entrar**
> en el estado cerrado del vocabulario —`resuelta`, ver la nota de vocabulario
> más abajo—, publicar hace un `git commit` de verdad en el repo de código que
> contiene `docs/wiki/`, sin que nadie lo pida a mano.
>
> - **Se activa por proyecto, nunca por defecto.** `wiki.json` declara
>   `"git_commit_al_cerrar_incidencia": true`; si no está, vale `false` y
>   `publicar.py` se comporta exactamente como antes de esta regla. Un
>   proyecto que ya usa la skill no ve cambiar su comportamiento porque la
>   skill aprendió una capacidad nueva — mismo criterio que `mapas_de` o
>   `incidencias_de`: lo que depende del proyecto se declara en su manifiesto,
>   nunca se adivina ni se enciende solo.
> - **Quién firma, y qué NO se lleva (corregido 2026-09-14).** La coautoría
>   sale de `"coautoria_commit"` en `wiki.json` (o de `WIKI_COAUTORIA` en el
>   entorno); si no hay ninguna, el commit va **sin** trailer. La primera
>   versión llevaba «Claude Sonnet 5» escrito en el código: habría firmado con
>   un modelo que no trabajó el proyecto, en una historia que no se reescribe.
>   Y el commit se hace con `-- <rutas>`: sin la lista, `git commit` se llevaba
>   todo lo que hubiera en el índice, incluido lo preparado para otro commit.
> - **Qué entra en el commit.** Lo que la publicación acaba de tocar y **vive
>   dentro del repo de código**: `wiki.lock.json` (que ahora además guarda,
>   sólo si esta capacidad está activa, la `situacion:` observada de cada
>   incidencia — es el "antes" contra el que se mide la transición), el
>   `.base` del tablero de incidencias si el manifiesto lo declara, y el
>   `.canvas` fuente de cualquier mapa que la incidencia cerrada ancle por
>   `mapa_n`.
> - **Qué NO entra, y por qué — el mismo tipo de límite que la Regla 5
>   declaró para Alejandría.** La nota de la incidencia (el `.md`) vive
>   **sólo** en la bóveda: es manual por naturaleza (Regla 2) y el repo de
>   código no tiene working tree sobre `/mnt/f/OBSIDIAN`, así que no hay
>   fichero que darle a `git add`. El commit la **referencia** — `INC-###` y
>   su título corto, en el propio mensaje — pero no puede llevar su
>   contenido. Formato del mensaje:
>   `wiki: cierra INC-009 (título corto) — regenera mapa N y base de incidencias`.
> - **El vocabulario real es `resuelta`, no `cerrada`.** `situacion:` es el
>   vocabulario cerrado de `generar_incidencias.py`
>   (`abierta · en_curso · bloqueada · resuelta · descartada`); «cerrada» es
>   la palabra que se usa al hablar del concepto, no un valor válido del
>   frontmatter. `publicar.py` tiende ese puente en una sola constante
>   (`SITUACION_CERRADA`) para que el resto del código llame a cada cosa por
>   su nombre real.
> - **Alcance de esta slice, deliberadamente acotado — igual que Alejandría
>   en la Regla 5.** Esto es **sólo el commit**. Crear una rama por
>   incidencia y abrir un Pull Request **no** están implementados: quedan
>   anotados como pendientes, no como resueltos, y son la extensión natural
>   el día que alguien los pida — no el trabajo de hoy.
> - **Local no basta: lo que se commitea, se empuja a GitHub (añadido
>   2026-09-18, a pedido explícito del usuario).** Commits, pushes y releases
>   de un wiki repo no se quedan sólo en la copia local: se publican también en
>   el remoto de GitHub, para que el trabajo contribuya de verdad al repo.
>   La credencial vive en **`/mnt/f/src/api/api/github_personal_access_token.txt`**
>   (índice y reglas de uso en el `README.md` de esa carpeta) y se pasa **por
>   ruta, nunca por valor**: no se imprime, ni truncada, ni se copia a otro
>   sitio. Se verifica con `GET /user` (HTTP 200), no mostrando el token.
>   Con `gh`, autenticar leyendo el fichero por stdin
>   (`gh auth login --with-token < <ruta>`); con la API directa, cabecera
>   `Authorization` armada en el momento. Un release es `gh release create` (o
>   `POST /repos/{owner}/{repo}/releases`) sobre el tag ya empujado.
>   Reglas que no cambian: el push es a la rama del trabajo, **nunca `--force`
>   a main/master**, y si el PAT devuelve 401 se declara (puede estar
>   revocado, ya pasó) en vez de dejar el trabajo sólo local en silencio.
>   Rama por incidencia y Pull Request siguen siendo la extensión pendiente de
>   arriba; esto sólo cierra el hueco de que el commit no saliera de la máquina.
> - Ver `scripts/tests/test_publicar_commit_incidencia.py`: cierra una
>   incidencia sobre un repo git real (no mockeado) y comprueba el mensaje,
>   la atribución, qué ficheros toca el commit, y que una segunda publicación
>   sin cambios no lo duplica.

> **7. Los repos se hablan por incidencias. Un mensaje recibido se contesta
> en la misma sesión que lo ve, y uno necesario se envía, no se calla.**
> Añadida 2026-09-23, a pedido explícito del usuario: *«siempre debes
> comunicarte, es una forma de comunicación entre repos y proyectos, y
> atenderse a la brevedad»*. Nace de un fallo concreto: AJOLOTE dejó en el
> tablero de ATALANTA una petición bloqueante (re-pin tras reescribir su
> historial; **«AJOLOTE no hará el force-push hasta leer tu respuesta»**), y la
> sesión de ATALANTA que la encontró la aparcó como «decisión del usuario».
> El otro repo se quedó parado sin que nadie lo supiera.
>
> **Enviar (repo A necesita algo de repo B):**
>
> 1. **Origen en el tablero propio.** A escribe su incidencia (`INC-NNN` de A)
>    con lo medido, y una línea `**Canal:**` que enlaza el mensaje enviado.
> 2. **Mensaje en el tablero del destinatario.** A escribe una nota en
>    `Incidencias/` de B con **el siguiente `INC-` libre de B**. Hay que mirar
>    el disco antes, porque otro repo puede haberlo tomado en la misma hora
>    (pasó: INC-057). La nota lleva:
>    - `fuente: "mensaje de A → B. Origen: A INC-NNN (ruta)"`;
>    - arriba, `**Canal:**` diciendo dónde se responde;
>    - `## Qué pasa`, **medido**, con cifras y shas, nunca de memoria;
>    - `## Qué se pide a B`, **en preguntas numeradas** que se contesten sí/no
>      o con un dato;
>    - `## Casillas`;
>    - `## Respuesta de B`, con `_(vacío — escribe aquí)_`.
> 3. **Decir si bloquea.** Una línea: «no bloquea a A» o «A no hará X hasta
>    leer la respuesta». Sin ella, el receptor no sabe con qué prisa leer.
> 4. **Escribir en el tablero de B no es tocar a B.** El `.md` de la bóveda es
>    el buzón. El código de B, su `wiki.json` y su `publicar.py` **no se
>    tocan**: B indexa el mensaje la próxima vez que publique. Si a A le han
>    prohibido tocar B, esto sigue permitido, porque es un mensaje y no una edición.
>
> **Recibir (llega una nota con `fuente: mensaje de X → nosotros`):**
>
> 1. **Se contesta en la misma sesión que la ve**, aunque la tarea en curso
>    sea otra. «A la brevedad» significa hoy, no «cuando se cierre lo mío».
> 2. **Se responde en `## Respuesta de <nosotros>` de la nota recibida** y,
>    si el origen tiene su propia sección de respuesta, **también allí**, con
>    una línea y un enlace. El emisor puede estar mirando cualquiera de las dos.
> 3. **Breve, y lo primero es la respuesta**: «sí, adelante», «no, conservad
>    X» o «falta este dato». Después, punto por punto y con lo **medido en
>    disco** (sha, commit, qué fichero depende de qué). Luego se marca
>    `[x]` la casilla «responde».
> 4. **Si la decisión es del usuario, se contesta igual.** Se da todo lo que
>    se puede medir, se dice qué parte decide el usuario y se le avisa en el
>    chat. Nunca se deja el buzón en `_(vacío)_`: un silencio no se distingue
>    de «no lo he visto».
> 5. **Si la respuesta queda condicionada** («re-pinear sólo si el árbol
>    coincide»), la condición va escrita con el valor que se comprobará.
>
> Ejemplo real, 2026-09-23: AJOLOTE INC-010 ↔ ATALANTA INC-057 (recibido y
> contestado), y ATALANTA INC-058 → AJOLOTE INC-011 (enviado).

## La compuerta de legibilidad — y el defecto que la puso ahí

`canvas_lib.py` mide el canvas **antes** de escribirlo: ninguna etiqueta de
arista puede quedar tapada.

El primer canvas se publicó con columnas a **800 px** de paso, nodos de 620 y
grupos de 60 de padding: `800 − 620 − 2·60` = **60 px de corredor**. Obsidian
dibuja la etiqueta de una arista como una **caja** centrada en el punto medio de
la curva —y ese punto medio, para una bezier con tiradores horizontales, es
exactamente la media de las dos anclas: los términos del tirador se cancelan—.
Las etiquetas medían **188–248 px**, de tres a cuatro veces el corredor: **6 de
las 13 quedaron detrás de un nodo**.

Y la primera versión del validador comprobaba el **punto** medio, así que dio
verde con las seis ilegibles delante. Comprobar el punto no basta: hay que
comprobar la **caja**. De ahí la regla de este entorno: *una regla que no tiene
compuerta no protege nada*.

## Una Base filtra por una ruta, y la ruta depende de qué bóveda se abrió

⛔ Dos Bases se publicaron filtrando por
`file.inFolder("wiki/ELEMENT/Incidencias")` y salieron **vacías**. La ruta de un
filtro es relativa a la **raíz de la bóveda**, y ese disco tiene dos raíces que
contienen esa carpeta (una anidada dentro de la otra). Obsidian dibuja una tabla
en blanco y no dice por qué: es lo mismo que ve quien aún no tiene datos.

Lo que falló no fue la sintaxis: fue que `validar()` medía la *intención*
(«¿existe la carpeta y tiene notas?») en vez del *artefacto*. Hoy `en_carpeta()`
toma la carpeta **absoluta**, `raices_de_boveda()` mide en disco qué directorios
por encima tienen `.obsidian/`, se emite un `inFolder` por cada uno, y se rechaza
el filtro si desde alguna raíz no alcanza nada. **Una raíz de bóveda es un hecho
del disco: se mide, nunca se supone.**

⚠️ Y `base_lib` **rechaza en duro** una columna que ninguna nota declare. Añadir
una propiedad al esquema y sembrarla en las notas es **la misma operación**, o
no se publica nada.

## Cómo se hace, de principio a fin

0. **Leer el tablero.** `00 — Incidencias de <TITULAR>.md` primero, siempre —
   regla 0. Dice qué está abierto, qué está bloqueado y por qué, y qué nodo del
   mapa mira cada cosa. Dibujar sin haberlo leído es proponer trabajo que ya
   estaba propuesto, o pisar una decisión que ya se tomó.
1. **Medir antes de dibujar.** Los `grep`, `md5sum` y lecturas de artefacto van
   antes del layout. Un canvas hereda la exactitud del peor de sus números.
1·bis. **Escribir la incidencia** que sostiene lo medido, con su `mapa_n` y su
   `nodo`, y regenerar su índice. El mapa se dibuja **desde** el tablero; el
   tablero no se rellena después para justificar el mapa.
2. **`iniciar.py --aplicar`.**
3. **Escribir el generador** copiando `plantilla_generador.py`, y **declararlo**
   en `wiki.json` (`mapas[]` o `bases[]`).
4. **Generar y ensayar**:
   ```bash
   python3 docs/wiki/generar_<lo tuyo>.py docs/wiki/<lo tuyo>.canvas
   python3 docs/wiki/publicar.py docs/wiki --simulacro
   ```
5. **Enlazar desde la nota puerta** los índices que `publicar.py` dicte —da el
   renglón exacto— y publicar de verdad.
6. **Indexar en la bóveda en la misma operación** (`index.md` o el sub-mapa que
   corresponda) y correr `vault_audit.py`. Una nota que nadie enlaza existe en
   el disco y no existe para nadie.
7. **Cerrarlo con un test** que regenere cada artefacto y lo compare **byte a
   byte** con la copia del repo. Contra la bóveda no se puede: Obsidian
   reescribe el fichero con sólo abrirlo, así que ahí la comparación es de
   **huella canónica**.

## Layout — lo que la geometría por defecto ya resuelve

| parámetro | valor | por qué |
|---|---:|---|
| `paso` de columna | **1400** | deja **660 px** de corredor: cabe la etiqueta más larga necesitada (248 px) con aire |
| `ancho` de nodo | 620 | dos o tres frases por línea sin partir feo el texto |
| `padding` de grupo | 60 | el borde del grupo no pisa el nodo |
| `gap` vertical | 110 | las etiquetas de las aristas verticales caben entre nodo y nodo |

Cuando una arista **salta varias columnas**, su punto medio cae en una columna
intermedia: si la compuerta se queja, se acorta la etiqueta o se cambia de lado
(`bottom`/`top`). **No se estrecha el corredor.**

## Convenio de color

| color | significa |
|---|---|
| 🟪 `6` morado | arquitectura y doctrina |
| 🟦 `5` cian | dato o material de entrada |
| 🟨 `3` amarillo | compuerta, o trabajo por hacer |
| 🟩 `4` verde | verde hoy, con su cifra |
| 🟧 `2` naranja | declarado y publicado, **sin voto** (criterio sombra) |
| 🟥 `1` rojo | hueco, interruptor apagado o muleta |

## El tablero de incidencias

> **Es la puerta de entrada de todo lo demás — ver la regla 0.** Se lee antes de
> dibujar, y lo que se mide entra aquí antes que al lienzo.

**Dos numeraciones conviven, y no son lo mismo:**

| qué | cómo se llama | qué es |
|---|---|---|
| la serie de RFC | `01.…`, `02.…`, `03.<título> -<TITULAR>` | documentos que **deciden** una arquitectura |
| el identificador | `INC-001` … `INC-NNN` | único y estable, **nunca se reutiliza** |
| las casillas | `- [ ]` / `- [x]` en el cuerpo | lo que **cierra** esa incidencia |

Un fichero de la serie numerada **también** lleva su `INC-NNN`: `03.` es el
tercer RFC y puede ser `INC-025`. Los dos números son correctos y no coinciden;
citar «la #3» sin decir cuál es lo que hace falta desambiguar.

`generar_incidencias.py` publica la Base y el índice de `Incidencias/`. Una
incidencia es una nota con frontmatter:

```yaml
inc: INC-009          # identificador, único y estable
situacion: abierta    # abierta · en_curso · bloqueada · resuelta · descartada
tipo: rfc             # defecto · rfc · mejora  (vocabulario CERRADO)
peso: 5               # 1–5
mapa_n: 2             # a qué mapa apunta
nodo: l_sens          # (opcional) a qué nodo de ese mapa
bloqueado_por: ["[[otra incidencia]]"]
```

`tipo` existe porque **un RFC no es un defecto**: la plantilla de incidencia
pide decir *qué está mal*, y una propuesta de arquitectura no denuncia ninguna
falta. El índice cuenta además las casillas `- [ ]`/`- [x]` del cuerpo — pero
**sólo en el índice generado, nunca escritas de vuelta al frontmatter**: un
número derivado guardado en una nota viva se desincroniza en cuanto alguien
marca una casilla, y encima pisa lo que escribió una persona.

⚠️ El parser de frontmatter parte las listas en línea por comas, así que un
`[[enlace con, coma]]` dentro de `bloqueado_por` se pierde en silencio.

## Lo que esta skill NO hace

- **No decide qué es cierto.** Mide forma, legibilidad y consistencia; que el
  nodo diga la verdad depende de haber medido antes.
- **No dibuja sola.** El contenido y las agrupaciones son juicio de ingeniería.
- **No escribe el `index.md` del vault.** Comprueba que exista el enlace y exige
  que lo escriba quien conoce el gancho — un renglón de índice es un **gancho**,
  no un resumen.
- **No inventa carpetas.** Usa la convención que el vault ya tiene:
  `wiki/<PROYECTO>/`.

## Referencias

- `referencias/json-canvas.md` — el formato 1.0 entero, en una página.
- `scripts/iniciar.py` — estrenar y poner al día un wiki repo.
- `scripts/plantilla_generador.py` — esqueleto listo para copiar.
- `scripts/tests/test_vendorizado.py` — la copia es idéntica o no es una copia.
- `scripts/empaquetar.py` — arma el `.zip` para subir la skill a mano.

## Para subirla a mano

```bash
python3 /mnt/f/skills/_personales/_tools/empaquetar_skill.py <ruta de la skill>
```

La herramienta es **de la biblioteca, no de esta skill**: empaquetar no es la
capacidad de ninguna skill concreta, y tenerla dentro de una significaba que la
siguiente se estrellaría contra los mismos tres errores. Lo específico de cada
skill va en su `.empaquetado.json` — misma regla que hace vendorizable todo lo
demás de este disco. El de aquí saca `docs/` (es el wiki repo **publicado**, no
la capacidad, y su `.base` lleva raya larga) y recoloca el generador y el
manifiesto del mapa del sistema como `ejemplos/`.

Valida **antes de escribir nada** las reglas que costaron tres rechazos
seguidos, cada uno diciendo que algo está mal sin decir dónde:

| regla | lo que dijo el cargador |
|---|---|
| ningún nombre del zip fuera de ASCII | `Zip file contains path with invalid characters` |
| `description` sin `<…>` | `description cannot contain XML tags` |
| `description` ≤ 1024, **diciendo cuántos sobran** | `must be at most 1024 characters` |
| sólo `name`, `description`, `license`, `allowed-tools`, `metadata` arriba | — |

El tercero es el que enseña: la cifra estaba impresa en pantalla y nadie la
comparó. Un dato que hay que **acordarse** de comparar es un dato que un día no
se compara.

## Referencias

- `referencias/json-canvas.md` — el formato 1.0 entero, en una página.
- `scripts/iniciar.py` — estrenar y poner al día un wiki repo.
- `scripts/plantilla_generador.py` — esqueleto listo para copiar.
- `scripts/tests/test_vendorizado.py` — la copia es idéntica o no es una copia.
- `scripts/empaquetar.py` — arma el `.zip` para subir la skill a mano.

## Para subirla a mano: `empaquetar.py`, no un zip de la carpeta

Comprimir la carpeta entera y subirla devuelve `Zip file contains path with
invalid characters` **sin decir cuál**. El culpable es la raya larga (`—`) de
`docs/wiki/01 — Versiones de mapas de SISTEMA.base`, y ese nombre no se puede
cambiar: la numeración densa es la convención de la bóveda, y el `.base` del
repo tiene que llamarse igual que el publicado.

```bash
python3 scripts/empaquetar.py            # → ../wiki-de-proyecto.zip
```

Mete `SKILL.md`, `scripts/` y `referencias/` bajo una raíz `wiki-de-proyecto/`,
más el generador y el manifiesto del mapa del sistema como `ejemplos/` (nombres
ASCII). `docs/` se queda fuera: es el wiki repo **publicado**, no la capacidad.

**Y antes de escribir nada comprueba las cuatro reglas del cargador**, que son
las que costaron tres rechazos seguidos — cada uno diciendo que algo está mal
sin decir dónde:

| regla | lo que dijo el cargador |
|---|---|
| ningún nombre del zip fuera de ASCII | `Zip file contains path with invalid characters` |
| `description` sin `<…>` | `description cannot contain XML tags` |
| `description` ≤ 1024 caracteres | `must be at most 1024 characters` |
| sólo claves de la especificación arriba (`name`, `description`, `license`, `allowed-tools`, `metadata`) | — |

El tercero es el que enseña: la cifra estaba impresa en pantalla y nadie la
comparó. Un dato que hay que **acordarse** de comparar es un dato que un día no
se compara. `scripts/tests/test_empaquetado.py` prueba que la comprobación
**detecta** cada caso, y la suite de ELEMENT lo ejecuta.
