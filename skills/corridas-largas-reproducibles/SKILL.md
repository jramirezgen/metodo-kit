---
name: corridas-largas-reproducibles
description: "Diseñar y ejecutar cómputo científico caro (MILP, ODE, nulos por remuestreo, barridos) de forma que el resultado sea ATRIBUIBLE y no se pierdan horas. Úsala ANTES de lanzar cualquier tanda que dure más de unos minutos o que vaya a compararse con otra tanda: dónde colocar el paralelismo según el motor (el solver MILP paraleliza dentro, el integrador de EDO no), qué parámetros de ejecución son parte de la INSTANCIA y cambian el resultado aunque el flag determinista esté puesto, cómo indexar una caché cara para que no sobreviva a un cambio aguas arriba, cómo cronometrar de verdad, y cómo leer el dict que devuelve una simulación sin fabricar ceros en silencio. Cada regla trae la cifra que la costó."
version: 1.0.0
autor: "Kaitokid"
creado: 2026-09-05
---

# corridas-largas-reproducibles

Una tanda cara falla de dos maneras y las dos son caras: **tarda de más** (y se
recorta el diseño para que quepa) o **no es atribuible** (y hay que repetirla
entera). Esta skill es el conjunto de reglas que ya se pagaron, cada una con la
medición que la produjo. No es teoría de HPC: es la lista de lo que rompió.

## Regla 0 — el coste se mide con un cronómetro, no con una extrapolación

Antes de decidir el diseño de una tanda, se cronometra **un** caso real de esa
tanda. Extrapolar desde otro objeto es el error que más veces se ha pagado aquí.

| caso | lo que se extrapoló | lo que costó de verdad |
| --- | --- | --- |
| 200 brazos de EDO | «≈ 5 min», desde el cronómetro de una subred **restringida** de 321 reacciones (1.5 s) | **37 min**: el brazo del nulo debe CONTENER la ruta, así que corre sobre la subred casi entera (3053 − k) — otro objeto |
| un solve MILP | cronometrar `discover_routes` con `k_routes=1` | no mide nada: la primera ruta es la barata, y el coste vive en las iteraciones que buscan alternativas |
| un `integrate` de paisaje | cronometrarlo desde un punto ya convergido | 5e-05 s, artefacto puro: el integrador corta en `max|dx| < 1e-7`. Se mide **con señal**, como se va a usar |

## Regla 1 — el paralelismo va donde el motor NO lo pone solo

Es la regla que más reloj mueve, y depende del motor:

| motor | dónde paraleliza | cómo se corre |
| --- | --- | --- |
| **Solver MILP** (CPLEX/Gurobi) | **dentro**, en el árbol B&B | **un caso a la vez**, dejándole la máquina entera |
| **Integrador de EDO** (Radau/BDF sobre red dispersa) | **no paraleliza**: un núcleo | **N casos a la vez**, un hilo cada uno |
| **Réplicas de un nulo** | no paralelizan | N a la vez, un hilo cada uno |

**La trampa concreta, medida:** los trabajadores de EDO consumían **155 % de CPU**
—BLAS abriendo hilos dentro de un solve que no escala con ellos— así que 8
procesos ya saturaban 20 núcleos (load 16.6) y el ritmo era **2.4 casos/min**.
Fijando `OMP_NUM_THREADS=MKL_NUM_THREADS=OPENBLAS_NUM_THREADS=1` y subiendo a 16
procesos, cada trabajador bajó a **91.5 %** y el ritmo subió a **4.94 casos/min
(×2.06)**. El hilo de BLAS no estaba trabajando: estaba girando.

```bash
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
```

**Y no es sólo reloj — ver la Regla 2.** Trocear el solver MILP en 5 procesos ×4
hilos era más rápido *en apariencia* y además cambiaba el resultado. Corriendo de
uno en uno con los 20 hilos, el mismo brazo pasó de **67.8 s a 26.5 s**: el troceo
pagaba reloj *y* rompía la compuerta.

**Orden recomendado de una tanda mixta:** primero **todos** los solves MILP en
serie (cada uno con la máquina entera), después las simulaciones en grupos
paralelos de un hilo. No se mezclan: un solve con límite de tiempo de **pared**
compitiendo contra 16 procesos de EDO puede vaciarse por el cronómetro.

## Regla 2 — hay parámetros de ejecución que son parte de la INSTANCIA

El flag determinista **no basta**. Medición, con el vector de entrada byte a byte
idéntico (sha256 verificado), mismo modelo, misma máquina, `DETERMINISTIC=1`:

| comparación | Jaccard de la solución |
| --- | ---: |
| 4 hilos ↔ 4 hilos, dos tandas independientes | **1.000000** |
| 20 hilos ↔ 4 hilos | **0.854286** |
| 20 hilos ↔ 20 hilos (otra fase, meses antes) | **1.000000** |

O sea: **no es no-determinismo**. A configuración fija es exacto. Lo que cambia
es que el reparto de nodos del B&B entre hilos decide **cuál** de los muchos
óptimos dentro del `mip_gap` se encuentra primero. Las dos soluciones son óptimas
al criterio declarado; lo que no es estable es su **identidad** — y la identidad
era justo lo que la comparación medía. El 14.6 % de diferencia es del mismo orden
que el 20 % que ese mismo solver da entre dos corridas en modo *oportunista*.

**Regla operativa:** el número de hilos se **fija y se publica** junto al hash de
la entrada. Su valor por defecto suele ser `os.cpu_count()`, así que **la
instancia cambia de máquina a máquina sin que nadie escriba nada.**

⚠️ Distíngase del caso benigno: repartir **réplicas independientes y sembradas**
entre procesos no cambia ningún valor, porque cada réplica es determinista en su
semilla y no comparte estado. Subir de 6 a 16 procesos ahí es gratis. La pregunta
que separa los dos casos es: *¿el reparto entra en el cálculo de un solo caso?*

⛔ **Y hay que mirar qué default impone la CAPA, no qué default trae el solver.**
Verificado sobre el fuente de la librería de este programa: el modo paralelo
oportunista —el no determinista— **no es el default de CPLEX** (el suyo es
automático y determinista); lo pone la librería, con un `parallel.set(-1)` que sólo
se desactiva exportando una variable de entorno que **la CLI no expone y la
documentación no menciona**. Un default de la capa intermedia es tan parte de la
instancia como uno del solver, y se descubre leyendo, no suponiendo.

⛔ **La vía «estandarizada» puede ser precisamente la trampa.** En este programa la
plantilla del cuaderno canónico hace
`os.environ.setdefault('ELEMENT_CPLEX_THREADS', str(os.cpu_count()))`: el camino que
se recomienda a quien empieza **ata la solución al hardware de la máquina**. Que una
receta esté en el arranque oficial no la hace reproducible entre máquinas.

✅ **Antes de decir «lo hace en silencio», léase el log.** En este mismo caso yo
afirmé que el solver se comía todos los núcleos sin avisar, y es falso: emite
`threads=N/M` a nivel INFO, y el nivel INFO está activo por defecto. Estaba escrito;
no lo leí. Una acusación de silencio se comprueba con un `grep` al log, no de
memoria.

## Regla 3 — una caché cara se indexa por TODO lo que la determina

Una caché de 5 000 réplicas que cuesta 86 min indexada como
`nulo_B{B}_s{semilla}.npy` **sobrevive en silencio a un cambio del banco de datos
de entrada** y devuelve el resultado viejo sobre el mundo nuevo. No avisa, no
falla: acierta el nombre.

```python
huella = sha_file(ENTRADA)[:12]                    # lo que la caché realmente resume
dest = DIR / f"nulo_B{B}_s{semilla}_{huella}.npy"  # el nombre lo lleva encima
```

La regla general: **el nombre de un artefacto derivado contiene el hash de sus
entradas**, o el artefacto no es reanudable, es una trampa. Lo mismo vale para un
directorio de resultados reanudable por índice.

## Regla 4 — leer un dict de resultado sin `.get(clave, default)`

El defecto más caro de esta serie fue de una letra: la función **recibe** `track=`
y **devuelve** `tracked`. Leyendo `sol.get("track")` con un `zeros` de reserva
encima, el observable salía **idénticamente 0 en los 35 brazos** — y habría
disparado un veredicto pre-inscrito («el árbitro es degenerado») que era cierto
del código y falso del mundo.

```python
trk = sol.get("tracked")
if not trk:
    return {"VOID": "la simulación no devolvió `tracked`"}
falta = [k for k in PEDIDAS if k not in trk or np.asarray(trk[k]).size != len(sol["t"])]
if falta:
    raise SystemExit(f"ABORTA: `tracked` no trae {falta}")
```

**Un `default` en la lectura de un resultado es una fábrica de ceros silenciosos.**
Se aborta o se marca VOID; nunca se rellena. Y se verifica el **nombre exacto** de
la clave leyendo la función que la devuelve, no la que la recibe.

**Y el reverso, que es el mismo error con el signo cambiado.** Un `d[k]` crudo sobre
un artefacto sellado no fabrica ceros: revienta. El problema es *cuándo*. Medido en
F48: el módulo del veredicto leía `E1["G_BATCH"]["efecto_del_tamano_de_lote"]["max_abs_dif"]`
y la clave sellada era `b_efecto_del_tamano_del_lote` → `cota_sobre_T_arco_si_se_usara_lote`.
El `KeyError` esperaba **después** de 5 000 réplicas de un nulo (~100 min), 200 brazos
de EDO y 500 de LOO. Ninguna prueba de humo lo alcanza, porque esa línea sólo se
recorre en la tanda definitiva.

Dos costumbres lo cierran, y las dos son baratas:

1. **Auditar los accesos contra los artefactos ANTES de lanzar.** Un script que
   recorre cada lectura que hará el módulo de veredicto sobre los `.json` que ya
   existen, e imprime `OK` o `FALLA` por cada una. Cuesta segundos y cubre el camino
   entero, no el que la prueba de humo alcanza.
2. **Un `pide(d, *ruta)` que aborte nombrando la clave que falta**, en vez de un
   `d[k]` que aborta con una traza que no dice ni el artefacto ni la ruta:

```python
def pide(d, *ruta, ctx=""):
    cur = d
    for i, k in enumerate(ruta):
        if not isinstance(cur, dict) or k not in cur:
            raise SystemExit(f"ABORTA: falta {'.'.join(ruta[:i+1])} ({ctx}). "
                             f"Presentes: {sorted(cur)[:14]}")
        cur = cur[k]
    return cur
```

⛔ **Y la comprobación de que la reparación está puesta se hace por AST, no por
subcadena.** La primera versión de esa guarda en F48 hizo `clave_vieja in fuente` y
dio falso negativo: la clave vieja seguía escrita **en el comentario que la
documenta**. Un comentario no es una lectura. Se recorren los nodos `Subscript` con
clave literal.

## Regla 4b — el orden de ejecución tiene que respetar el grafo de `consume`

Si un módulo declara `consume: {"X.json": sha}`, entonces **corre después de X**, y
eso hay que leerlo del grafo, no de la intuición de en qué orden «tocan» los pasos.

Medido en F48: el guion de la tanda corría `enmienda03` en el paso 3 y `E1`/`E3` en
los pasos 4 y 5, porque la enmienda «era una corrección y va antes». Pero
`enmienda03` **consume** `E1` y `E3`. Resultado: la enmienda se selló a las 03:05:22
declarando shas de un `E1` y un `E3` que se re-sellaron a las 03:06:04 y 03:06:17, o
sea que la cláusula del veredicto que salía de ella se calculó sobre **el banco
anterior a la reparación**. El re-cálculo tardó 30.7 s y cambió el orden medido, lo
que confirma que el artefacto viejo no era el de ese banco.

Dos guardas, y la segunda es la que de verdad lo caza:

- **Cierre transitivo hacia adelante**: se ancla el CONSUMIDOR de algo ya anclado.
  (El error fácil, y el que traía el registrador heredado, es anclar lo *consumido*.)
- **`consume` con sello caduco = abortar.** Si `D[m]["sha256"] != d["consume"][m]`,
  el insumo se regeneró después. No es un aviso: es que el artefacto habla de otra
  corrida.

```python
caducos = [f"{n} consume {m} con {v[:12]}, vigente {D[m]['sha256'][:12]}"
           for n, d in D.items() for m, v in d.get("consume", {}).items()
           if not m.startswith("_") and m in D and D[m]["sha256"] != v]
if caducos: raise SystemExit(f"ABORTA: sellos caducos: {caducos}")
```

Y para lo que **no** declara `consume` y aun así decide —en F48, los 200 brazos que
alimentan uno de los tres nulos— la salida no es la fecha del fichero: es verificar
**por contenido** que comparten la rejilla y el objeto del banco vigente. La fecha
acompaña; no decide. Sobre todo si el módulo es reanudable, que es justo cuando un
fichero nuevo puede tener dentro un cálculo viejo.

## Regla 5 — una reparación omitida caduca cuando caduca su demostración

Un paso de saneamiento del que una fase anterior demostró que era innecesario
(«en este modelo esa función devuelve el conjunto vacío, y aquí está la compuerta
que lo prueba») **se copió sin la compuerta** a una fase que había cambiado el
modelo. Resultado medido: 3 y 2 fuentes espurias, y un balance de masa con
**+104 %** y **+198 %** de exceso — el sistema fabricaba lo que decía consumir.

**Regla:** al copiar una línea de una fase anterior, se copia también **la
condición bajo la que era correcta**, y se convierte en compuerta. Si la
demostración estaba atada al dato y el dato cambió, la omisión ya no vale.

## Regla 5b — una prueba de equivalencia caduca cuando se re-corre cualquiera de sus dos lados

Esta es la versión de la Regla 5 que **ninguna compuerta de sellos atrapa**, y por
eso hay que buscarla a mano.

Para poder correr 35 brazos en minutos en vez de en 14 horas se instaló un atajo
en el motor y se demostró que era **inerte**: se corrieron 6 brazos por los dos
caminos y se comparó ruta a ruta, `TODOS_IDENTICOS = True`. La prueba se selló.
Tres horas y media después la cadena definitiva **volvió a correr esos mismos
brazos** con otro número de hilos, y sobrescribió el directorio de salida que la
prueba había leído. Medido después: los **seis** brazos difieren en la unión de
reacciones (uno pasa de 331 a 356) y todos tardan la mitad. La prueba no estaba
mal — **su objeto había sido sustituido**.

La consecuencia es la que importa: el atajo es lo que produjo la tanda definitiva,
así que la licencia de esa tanda era una demostración sobre **otra** tanda. No
falsada: **sin licencia**, que es distinto y peor de dejar sin decir.

**Por qué el sello no lo caza.** La disciplina normal —cada artefacto declara un
`consume` con el sha256 de lo que leyó, y una compuerta aborta si algún `consume`
apunta a un sello caduco— cubre los `.json` sellados. Aquí la evidencia era un
**directorio de salida**, que ningún sha cubre.

**Regla:** si una prueba depende de ficheros que no son artefactos sellados, o se
sella el directorio (sha del conjunto), o la prueba se **re-deriva cada vez que se
re-corre cualquiera de las dos cosas que compara**. Y si lo que cambió entre las
dos corridas es un parámetro que la Regla 2 declara parte de la instancia (aquí,
los hilos), re-derivarla mal es peor que no re-derivarla: compararía **ese
parámetro**, no lo que se quería probar.

## Regla 5c — antes de atribuir el hallazgo al modelo, mide la ganancia del modelo

El estadístico que decidía la fase era la longitud del arco de la trayectoria que
sale de un integrador no lineal, contra 5000 réplicas nulas: `p = 0.0002`, con el
real por encima del **máximo** de las 5000 y `z = 5.77`. Todo correcto — el nulo
no está degenerado, la cardinalidad está emparejada, la p es real.

Y aun así la frase «el modelo distingue la señal buena» habría sido **falsa**.
Medido el arco de la señal de **entrada** y el de la trayectoria de **salida**, la
ganancia es **1.0036**: el integrador transmite la entrada casi intacta. Lo que
discrimina vive **aguas arriba**; el modelo es un pasamanos.

Lo instructivo es que la propia fase ya tenía las dos cifras que lo implicaban
—un test de superposición por debajo de su piso, y un parámetro interno que decía
que el punto de trabajo es localmente lineal— y ninguna de las dos estaba
conectada con la lectura del resultado.

**Regla:** cuando el estadístico que decide se mide a la **salida** de un modelo,
mídelo también a la **entrada** y publica el cociente. Si el cociente es ~1, el
hallazgo es del dato, no del modelo — y hay que decirlo en la misma frase en que
se da la p, no en una nota al pie.

## Regla 5d — un relanzador que espera a un PID tiene que ser singleton

Se lanzó dos veces el mismo script «espera a que muera el PID N y relanza». Los
dos esperaban al mismo PID, así que los dos arrancaron a la vez **la misma tanda**
sobre las mismas cachés, con 2 × 13 procesos peleándose por 20 núcleos, y ambos
apuntando a escribir **el mismo artefacto sellado**. Se detectó por `ps`, no por
ningún aviso: los dos logs parecían normales por separado.

**Regla:** un relanzador lleva **fichero de bloqueo** (`flock` o un `.pid` que se
comprueba antes de arrancar), o no se lanza dos veces. Y antes de dar por buena una
tanda larga, `ps` una vez: dos procesos escribiendo el mismo `.json` no dan error,
dan el que acabe último.

## Regla 5e — antes de declarar que dos cifras chocan, corre la función a la tolerancia de la otra

Una compuerta de coherencia avisó de que la fase publicaba **5.709** para una
constante que el registro canónico fija en **5.616 ± 0.05**. Con las dos cifras
delante parecía un choque que había que declarar y arbitrar.

No lo era. La función que las produce **biseca y devuelve el extremo superior** del
intervalo —o sea una **cota superior**, no el valor— y su tolerancia **por defecto**
es 0.25, cinco veces más gruesa que el 0.05 con que se fijó la canónica. Corriendo
**la misma función sobre el mismo objeto** a `tol = 0.05` sale la canónica **bit a
bit** (5.615966796875), y a `tol = 0.01`, 5.6004638671875. Una medida, tres
resoluciones.

**Regla:** una cifra que sale de un procedimiento iterativo **no es un número, es un
número más su criterio de parada**. Antes de declarar que contradice a otra, (a) mira
si la función devuelve el valor o una **cota**, (b) mira su tolerancia **por defecto**
—que casi nunca es la que se usó para fijar la cifra de referencia—, y (c) **córrela a
la tolerancia de la otra**. Cuesta segundos y evita inscribir un choque que no existe.
Si tras eso sigue habiendo diferencia, entonces sí: se declara, no se maquilla.

⚠️ El corolario para el que publica: al sellar una cifra de bisección, publica **la
tolerancia junto al número**. Sin ella, la cifra no es reproducible ni comparable.

## Regla 6 — un motivo de fallo sin rama es un motivo sin nombre

Un `return None` con tres causas distintas (biblioteca ausente, límite de
licencia, veredicto de estado) llega al que lo consume como un `None` y el aborto
no sabe decir por qué. Se parsea el log y se le da **una rama a cada causa**, con
la línea del fuente citada al lado. Un aborto que no nombra la causa obliga a
repetir la tanda para averiguarla.

## Regla 7 — el reloj que no aparece en el perfil del solver

Un *fallback* de construcción del modelo tardaba **613.9 s antes de resolver
nada** (objetivo 435.6 s + restricciones de balance 171.5 s), y era invisible en
los registros del solver porque ocurría **antes** de entrar en él. Se descubrió
cronometrando la construcción por separado, no el solve. Además su
`solver_timeout` no se aplicaba nunca (`'Model' object has no attribute 'config'`)
y fallaba **en silencio**.

**Regla:** cronometrar por separado *construcción* y *resolución*. Un límite de
tiempo que no lanza excepción cuando no se puede aplicar es un límite que no
existe.

## Lista de comprobación antes de lanzar una tanda cara

1. ¿Cronometré **un caso real de esta tanda**, no de otra parecida?
2. ¿El paralelismo está donde el motor **no** lo pone solo? ¿Fijé los hilos de BLAS?
3. ¿Qué parámetros de ejecución entran en el cálculo de **un** caso? ¿Están fijados y publicados?
4. ¿El nombre de cada artefacto reanudable lleva el hash de sus entradas?
5. ¿Alguna lectura de resultado tiene un `default`? ¿Alguna clave la copié de la firma de entrada?
6. ¿Copié alguna omisión de otra fase sin copiar la compuerta que la justificaba?
7. ¿Alguna prueba de equivalencia lee un **directorio** en vez de un artefacto sellado? ¿Se ha
   re-corrido cualquiera de sus dos lados desde que se selló?
8. Si el estadístico que decide sale de un modelo: ¿medí también el de **entrada**? ¿Publiqué el
   cociente en la misma frase que la p?
9. `ps` antes de irse: ¿hay **un** proceso escribiendo cada artefacto, o hay dos?
10. ¿Los solves con límite de **pared** corren sin competencia?
11. ¿Alguna cifra mía sale de una **bisección**? ¿Publiqué su tolerancia? Y si contradice a una
    de referencia, ¿la corrí a la tolerancia de esa antes de llamarlo choque?
