# Lecciones de arquitectura que una revisión adversarial encontró y la autoevaluación no

> Origen: AQUERONTE, 2026-10-03. Dos autoevaluaciones seguidas dieron **10/10**. La
> primera revisión adversarial independiente dio **5/10** con 18 hallazgos (4
> bloqueantes), y los **18 resultaron ciertos** al comprobarlos contra el texto.
>
> La **segunda ronda**, sobre la versión ya corregida, volvió a dar **5/10**: de los
> 18 cierres sólo 4 lo eran de verdad. Lo que añadió está en la sección **H**, y
> enmienda A2, A4, A6 y C2.
>
> Aquí está lo que generaliza, escrito para **cualquier** proyecto. Se abre al
> diseñar un proyecto nuevo y antes de puntuar un diseño. Cada lección dice qué
> falla, cómo se detecta y qué mecanismo lo cierra. **Un cierre que es sólo prosa
> no cuenta:** tiene que haber un test, un hook o un generador que se niegue.

## A. Validación honesta: lo que construye no puede ser lo que juzga

Pesan más en proyectos científicos y de ML, pero valen para cualquier sistema que
se evalúa contra datos.

| # | Falla | Cómo se detecta | Mecanismo que lo cierra |
|---|---|---|---|
| A1 | **Un dato juez usado como entrada.** Basta con que el catálogo de fuentes diga «calibra», «ancla» o «para los parámetros» sobre un dataset que luego valida | Leer cada fila del catálogo preguntando: *¿este dato también aparece en un criterio de éxito?* | **Tabla cerrada de roles** por huella y DOI: `entrada \| juez \| contraste \| vetado`, nunca dos a la vez. El juez rechaza cualquier entrada cuya procedencia tenga rol juez |
| A2 | **El linaje sólo caza copias de bytes.** El canal real de fuga es el **agente** (humano o IA): transcribe una cifra que ya vio, elige un umbral mirando el resultado, ajusta un ruido a las fracciones que luego juzgan | Preguntar por cada constante: *¿quién la eligió y qué había visto antes?* | Toda constante estipulada declara `jueces_vistos`, y se guardan huellas de **valor**, no sólo de fichero. El agente cuenta como capa del sistema. ⚠️ **No basta (H3):** la declaración es informativa; la ceguera se garantiza por separación física |
| A3 | **Un sha no prueba que la preinscripción fue antes.** Un hash dice qué se escribió, no cuándo | ¿Puede la corrida existir en git antes que su criterio? | La preinscripción se commitea y empuja, y el juez exige `git merge-base --is-ancestor <preinscripción> <corrida>`. En el DAG, una corrida que no desciende de su preinscripción **no se genera** |
| A4 | **Iterar contra el mismo juez es selección de modelo encubierta** | «No son compuertas, se itera»: ¿contra qué datos se itera? | Cada juez se parte en **desarrollo** y **confirmación**. Las consultas se cuentan, y la confirmación se abre una vez por release. ⚠️ Ver H2: un juez compartido por varios criterios se gasta en el primero |
| A5 | **Un criterio de éxito se cumple por construcción.** La entrada ya contiene la respuesta, como un sensor sacado de la base de datos que define el fenómeno | ¿Pasaría el criterio un modelo trivial o aleatorio? | **Control negativo** obligatorio (un modelo que no debe pasar) y una vía independiente de la que dio la entrada |
| A6 | **Una constante no derivable decide el veredicto** | ¿Cambia el veredicto con ×0,5 o ×2 de la constante? | **Banda de sensibilidad obligatoria.** Un veredicto que cambia dentro de la banda se escribe «sensible a X» y no declara éxito. ⚠️ Ver H9: la banda ×0,5/×2 con centro libre es manipulable |
| A7 | **Un negativo se escribe como imposibilidad** | ¿Se acotó la búsqueda? | Presupuesto de búsqueda declarado. Se escribe «no encontrado con N arranques», nunca «no existe» |

## B. El plan es un dato, y la memoria falla antes de lo que parece

| # | Falla | Mecanismo |
|---|---|---|
| B1 | El plan en prosa se contradice con el plan en DAG, por ejemplo con un nodo «hecho» sobre una dependencia sin hacer | **Plan como datos** (`plan.json`) generado por un script que **se niega a escribir** si hay ciclo, dependencia inexistente, estado no monótono o un `hecho` sin un commit de evidencia que exista. Las reglas viven en **un** módulo, y lo usan el generador, el test y el «¿qué sigue?» |
| B2 | Cada documento usa su propio vocabulario de estados (`resuelto`, `hecho`, `cerrado`) | Vocabulario cerrado y único, validado al generar. Para la ciencia hace falta un estado **juzgado**, que desbloquea sea cual sea el veredicto, o los «no son compuertas» acaban funcionando como compuertas |
| B3 | Cifras escritas a mano en la prosa («99 nodos») que ya cambiaron | Ninguna cifra que el código puede contar se escribe a mano. Se genera o no se dice |
| B4 | Una regla que nunca se vio fallar | Test que **siembra cada defecto** y comprueba que la regla muerde |
| B5 | La memoria automática de un proyecto hermano entra en la sesión de otro | Hook con cwd propio. La prueba de fuego de la memoria es una sesión fría con un resumen de chat sembrado que contradice el disco: tiene que seguir el disco |

## C. Integración entre repos

| # | Falla | Mecanismo |
|---|---|---|
| C1 | **Un pin que no está en ningún remoto.** Funciona en la máquina y es imposible en un clon o en la CI | `git branch -r --contains <pin>` antes de fijarlo. Si sale vacío, se fija la release publicada más cercana y se comprueba con `git diff` que lo usado es idéntico |
| C2 | La dependencia ya validó contra los mismos datos que tú vas a usar como juez | Pedir por incidencia, en el tablero del **otro** repo, sus `jueces_vistos` con sha256 **y el módulo y la línea donde los usa**. Lo que la dependencia ya usó queda **quemado** (H4): ni entrada ni juez |
| C3 | Dos repos lanzan corridas pesadas a la vez en la misma máquina | Candado común (`flock /tmp/corrida_pesada.lock`) acordado por incidencia, no impuesto |
| C4 | Herencia «tabula rasa» que no lo es: la ecuación o la constante vienen del proyecto anterior | Herencia **declarada** en una decisión, con su origen. Trinquete de nombres legacy **por límite de palabra** y con lista blanca. Sin el límite, prohibir `element` también prohíbe «pasos elementales» |

## D. CI e higiene de git

| # | Falla | Mecanismo |
|---|---|---|
| D1 | Un test de historial en un clon superficial no ve historia y pasa en vacío | `fetch-depth: 0`, y un test que **falla** si `git rev-parse --is-shallow-repository` dice `true` |
| D2 | Se revisa el autor de los commits pero no el committer | El test y el `pre-push` miran autor **y** committer |
| D3 | El lockfile no fija los hermanos editables | En la CI los hermanos van por commit (dependencia git), no por ruta local |
| D4 | La reproducibilidad depende de BLAS y de la caché | `threadpoolctl` forzado en la composición. La clave de caché es **transitiva**, porque incluye las huellas de las entradas de las entradas. Las identidades que flotan se emparejan entre versiones (valles, clusters) por continuidad, no por cercanía |

## E. Modelado y nombres

| # | Falla | Mecanismo |
|---|---|---|
| E1 | **Colisión de nombres** con un término del dominio (`Sistema` frente a «sistema (M,R)», `Ruido` frente a «ruido» como significado) | Glosario que cubre **todos** los tipos públicos, sin tope de N términos. Un test cruza nombres de tipos contra el glosario |
| E2 | Una magnitud depende de una elección no declarada: unidades, coordenadas, medida de la cuenca | Declarar la elección en el tipo, y no comparar nunca entre elecciones distintas |
| E3 | Una variable de la ecuación sin definir (`m` frente a `m_g`), que si sale de una medida mete al juez | Cada símbolo de una ecuación del diseño lleva definición, procedencia y si puede o no venir de datos |
| E4 | Una ley no derivable con esquinas (`min`, `max`, `abs`) dentro de un solver de Newton o de una continuación | Versión **suave** como ley por defecto. La esquinada queda como variante de contraste, fuera del solver |
| E5 | El tipo juez filtra hacia el núcleo, porque la medida es importable desde el dominio | Tipo de medida **opaco** dentro del contexto de juicio, y un deserializador que lo rechaza fuera de un veredicto |

## F. Sobreingeniería: la pregunta que la detecta

**¿Cuántos nodos hay antes de la primera evidencia científica o de producto?** En
AQUERONTE eran 59. La respuesta fue meter **picos tempranos** (spikes) que prueban
la hipótesis más arriesgada justo después del mínimo de infraestructura, y sacar
del camino crítico lo que sólo hace falta para la release.

**Discrepar también es válido** si se declara. La API pública se quedó en el camino
porque sin ella la separación presentación/aplicación se rehace después.

## G. La revisión misma

- Los cierres los escribe el mismo autor que los defectos. **Hace falta una segunda
  ronda adversarial** sobre la versión cerrada antes de pasar de «8 estimado» a 10.
- Cada hallazgo del revisor se **verifica contra el texto** antes de aceptarlo.
  Un revisor también puede inventar.
- Lo aceptado entra con número en el tablero y en el DAG, y la sección del diseño
  enlaza cada cierre a su hallazgo: `#, severidad, comprobado contra, cierre`.
- Lo que se tachó en el diseño **se tacha, no se borra**. Que un texto erróneo
  existió es parte de la evidencia de que se corrigió.

## H. Lo que encontró la segunda ronda (sobre la versión ya «cerrada»)

La primera ronda cazó lo que faltaba. La segunda cazó **cierres que no cerraban**:
reglas que se burlan reetiquetando, decisiones que rompen otra decisión, y
mecanismos que piden al agente algo que no puede cumplir con honestidad.

| # | Falla | Cómo se detecta | Mecanismo que lo cierra |
|---|---|---|---|
| H1 | **Un término nuevo rompe un invariante del que dependen otras piezas.** Ejemplo: la dilución por crecimiento `−µx` destruye las leyes de conservación, y con ellas la «clase de compatibilidad» que usaban otros tres criterios | Al añadir un término a una ecuación, listar cada invariante que el resto del diseño **da por hecho** y comprobarlo sobre la ecuación nueva | Una decisión explícita sobre qué conserva y qué no. **El invariante se escribe como test** (`ℓᵀF(x) = 0` en puntos aleatorios), no como frase |
| H2 | **Un juez compartido se gasta en el primer criterio.** Si tres criterios y una banda de 9 puntos consultan la misma partición de confirmación, salen 27 consultas | Contar, por partición, cuántos criterios × vías × puntos de banda la abren | Subconjuntos de confirmación **disjuntos** por criterio. **Una consulta = un veredicto agregado**, con todas las vías y toda la banda dentro. Los criterios que comparten juez se juzgan en releases distintas |
| H3 | **Un control que pide al agente declarar lo que vio no se puede cumplir.** El agente conoce los datos por su entrenamiento y porque el plan le obliga a leerlos. O declara todo y nada se juzga, o no declara y nada lo detecta | ¿Este control depende de que el agente se acuerde y sea honesto sobre sí mismo? | **Separación física:** la partición de confirmación va cifrada con una clave que tiene el humano, y sólo la abre un comando de un solo uso. Los canales que no se pueden cerrar (entrenamiento, lectura de fuentes) se **declaran en Limitaciones**. La declaración queda como dato informativo, no como compuerta |
| H4 | **Heredar de una dependencia quema sus jueces, también los que vienen en sus plantillas por defecto.** Ejemplo: la reacción de biomasa de un GEM «a initio» es la de *E. coli* para todo Gram−. La dependencia los usaba como **entrada** en módulos que nadie había abierto | Abrir el código del pin, no su README. Preguntar a la dependencia, en su tablero, por cada dataset con huella, módulo y línea, y por sus plantillas | Rol **quemado** en la tabla de roles: ni entrada ni juez. La herencia se limita por decisión a **código** de primitivas, y se prohíben nominalmente sus constantes, tablas y estados de referencia. Lo que no se puede evitar (la plantilla) se declara y se contrasta con una alternativa |
| H5 | **Una regla que se aplica por etiqueta se burla cambiando la etiqueta.** Cambiar el `tipo` de una corrida a `spike`, o quitar un eureka de su `cubre`, y la regla de orden deja de aplicarse | Sembrar el reetiquetado en una copia del plan | El generador compara con el **plan commiteado** (`git show HEAD:plan.json`): un nodo juzgable no puede cambiar de tipo ni perder un criterio salvo que figure en una lista de **degradaciones declaradas** con motivo. Un tipo nuevo (`insumo`) para lo que de verdad no abre ningún juez |
| H6 | **La evidencia de «hecho» es cualquier commit.** Un sha que existe no prueba que ese commit entregó el nodo | ¿El commit citado toca alguna ruta de la entrega del nodo? | La regla extrae las rutas de la `entrega` y exige que el commit de evidencia toque al menos una. `juzgado` sólo en nodos de criterio y con veredicto obligatorio |
| H7 | **Un test escribe en el repo.** El test del plan regeneraba `plan.json`: ensuciaba el árbol y la segunda corrida pasaba siempre | Correr la suite dos veces sobre un árbol limpio y mirar `git status` | El generador tiene un modo `--comprobar` que compara sin escribir. Ningún test escribe dentro del repo |
| H8 | **Una ley con pesos normalizados la domina el término más grande, y depende de cómo se agrupan los términos.** Ejemplo: el mantenimiento energético (~54) se lleva casi todo el peso y un precursor traza nunca limita. Además faltaba un factor de conversión de unidades | Análisis dimensional de cada término. ¿Cambia el resultado si se reagrupa o se expande la entrada? | Pesos en una magnitud física (masa), sin los términos que no son precursores. El factor de conversión, con procedencia. **Test de invariancia** ante reagrupar. Las igualdades que salen por construcción se declaran como identidades de escala, no como resultados |
| H9 | **La banda de sensibilidad es manipulable.** ×0,5/×2 alrededor de un centro que elige el agente, cuando la incertidumbre real es de órdenes de magnitud, y sin las constantes que de verdad deciden | ¿Quién eligió el centro y cuándo? ¿Están en la banda **todas** las constantes que mueven el veredicto? | Rejilla **logarítmica** de al menos ±1 década, por parámetro (LHS si son muchos). **Centros preinscritos** antes de ver ningún resultado. Umbral de robustez declarado (≥80 % de la rejilla) |
| H10 | **El acierto lo explica un término global, no el mecanismo que se quería probar.** La dirección de expresión la fijaba el crecimiento, igual para todos los genes, y no la señal específica | ¿Qué daría una línea base que sólo tenga el término global? | Puntuar sólo donde actúa el mecanismo, con un observable centrado, y con la línea base del término global como comparación obligatoria |
| H11 | **Un pico de exploración corre lo mismo que el juez antes de la preinscripción** | ¿El spike produce algo que luego influya en el criterio? | El spike responde sí o no, su salida no se conserva y no abre particiones. Si hace falta más, la preinscripción va antes |
| H12 | **Un hook que sólo mira el mensaje** deja pasar un autor o committer `Claude <x@anthropic.com>` o un trailer `Assisted-by` | Probar el hook en un clon con un autor sembrado | Dos patrones versionados: uno de **identidad** (nombre y correo de autor y committer) y otro de **atribución** (mensaje). El test de historial y el `pre-push` usan los dos |
| H13 | **Un componente duplica la regla en vez de importarla.** El dibujo del plan tenía su propio «cerrado» y su propio «listo», y no validaba | Buscar la constante de vocabulario en todo el repo | Todo consumidor importa la regla de su módulo único y **se niega a dibujar** un plan inválido |

**La lección de fondo de la segunda ronda:** un cierre escrito por el mismo autor
tiende a **renombrar** el problema en vez de cerrarlo. Lo que sobrevivió fueron los
cierres con un ejecutable que muerde. Al pedir una ronda adversarial, pídele al
revisor que **siembre defectos** en una copia y que abra el código de las
dependencias, no sólo los documentos. Y que el autor no ponga cifra a su propio
cierre: el 10 lo da una ronda sin bloqueantes más la bala trazadora corriendo.

## I. Lo que encontró la tercera ronda (la nota bajó: 5 → 4)

| # | Defecto | Pregunta que lo detecta | Cierre |
| --- | --- | --- | --- |
| I1 | **Con datos públicos no hay ceguera que garantizar.** Un cifrado que escribe el mismo agente que predice, sobre un dato que ya conoce por su entrenamiento, es teatro | ¿El dato del juez es público? ¿Quién escribe el código que lo parte y lo cuenta? | Llamarlo por su nombre: **predicción preinscrita**. La regla de partición y el criterio se sellan y se empujan **antes** de descargar el dato; cada consulta se cuenta; la segunda sobre el mismo subconjunto no puede declarar éxito; tras un fallo, sólo datos nuevos |
| I2 | **La superficie heredada arrastra dependencias transitivas.** Una lista blanca de módulos «de forma» importaba módulos que cargan datos quemados | Importar el adaptador en un proceso limpio y listar `sys.modules` | Superficie mínima por **función**, no por módulo; test sobre `sys.modules` tras importar el adaptador |
| I3 | **Los valores por defecto de una dependencia son constantes heredadas.** Una función de estructura devolvía también parámetros por defecto calibrados en el otro repo | ¿Qué devuelve la función además de lo que pediste? | Descartar el resto dentro del adaptador y comprobar con huellas de valor que no llega al dominio |
| I4 | **El diseñador también se contamina.** Verificar un hallazgo leyendo el código interno del hermano dejó vistas sus constantes, y la decisión siguiente las repitió llamándolas «de libro» | ¿El autor de la decisión vio el valor antes de elegirlo? | Lo visto se declara **herencia** en una lista cerrada (`herencias.json`), nunca como elección independiente. Lo que haya que comprobar de un hermano se pregunta por su tablero, no leyendo su código |
| I5 | **Una ley de conservación por lista no escala.** Eximir «las moieties» funciona con 30 especies; en un modelo genómico el espacio nulo izquierdo tiene cientos de dimensiones y los cofactores no caen en ninguna | Calcular la base del espacio nulo izquierdo en el modelo **real**, no en el de juguete | Regla **estructural** (poda de subredes sin salida + soporte de las ℓ), la misma en el núcleo y en el genoma |
| I6 | **Bandas por décadas sobre parámetros sin rango físico**, y dos reglas de robustez distintas en el mismo documento | ¿El rango de cada parámetro tiene sentido físico? ¿Cuántas reglas de robustez hay escritas? | Rango físico por parámetro, una sola regla (≥ X % de N muestras, para positivo **y** negativo) y N presupuestado con un coste medido |
| I7 | **Un plan validado contra HEAD se burla commiteando generador y plan juntos**, y borrar un nodo no se compara con nada | Commitear en un clon un reetiquetado junto con su generador y correr la suite | Validar **toda la historia** del plan; las degradaciones viven dentro del plan y sólo crecen; borrar es una degradación |
| I8 | **El denominador lo elige el modelo.** Puntuar «sólo sobre los genes donde el modelo tiene mecanismo» deja que el modelo escoja dónde se le juzga | ¿Quién fija el conjunto evaluado, y cuándo? | Conjunto preinscrito antes de correr; lo que el modelo no cubre recibe la predicción de la línea base, no se excluye |
| I9 | **Un hook que falla abierto.** Con un sha remoto desconocido (push forzado) `git log a..b` fallaba y el push pasaba | Probar el hook con un sha remoto inexistente | Sha desconocido → revisar toda la historia; cualquier error de git aborta. Test en un repo temporal |

**La lección de fondo de la tercera ronda:** los bloqueantes ya no eran de código
sino de **honestidad epistémica** — qué sabe quién y cuándo. Los mecanismos que
prometen ceguera, independencia o «forma de libro» se rompen en cuanto se
pregunta quién escribió el mecanismo y qué había visto antes. Lo que sobrevive es
**declarar** el canal (herencia, predicción preinscrita, limitación con sus
consecuencias acotadas) y sellar en el tiempo lo que sí se puede ordenar.
