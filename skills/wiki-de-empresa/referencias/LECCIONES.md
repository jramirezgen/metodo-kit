# Lecciones del primer cliente (SAPYRIA, 2026-10-12)

Cada una costó una corrección medida. Se aplican al montar la próxima empresa.

1. **«Asistente de investigación» no basta como encuadre legal.** Una propuesta redactada para el paciente describe, de hecho, una venta directa. El encuadre (a quién se contrata, quién factura, quién toma) se decide **antes** de redactar la propuesta. La ronda 3 lo encontró como bloqueante.
2. **Una promesa de plazo sin fuente se queda en la propuesta.** «≈15 días» para un trámite no verificado llegó hasta el texto del cliente. Regla: ningún plazo de tercero sin confirmación escrita.
3. **Los riesgos se prueban combinados, no de uno en uno.** Cada riesgo aislado dejaba el margen ≥5 %; combinados bajaban a −15,4 %. Un «piso» sin escenario conjunto es una afirmación falsa.
4. **Una norma «de memoria» se marca con su confianza.** El DL 1669 acortó la ventana de 12 meses y la estrategia la daba por vigente. Buscar la norma vigente **antes** de escribir el plazo.
5. **La compuerta que valida la forma no valida el hecho.** Un `ref` con la forma correcta pasaba aunque el documento no existiera, y cualquier rol firmaba cualquier evidencia. Atar cada evidencia a su firmante y a su existencia en disco.
6. **La precedencia de operadores anuló un filtro de PII.** `A and B or C` dejó pasar un DNI con prefijo. Toda compuerta de seguridad se reescribe como función con paréntesis explícitos y se prueba con casos adversariales, no solo con los felices.
7. **La investigación asistida es insumo, no verdad.** Existían siete documentos de «modelo de negocio» sin verificar; rehacerlos habría perdido el trabajo y creerlos habría trasladado errores. Inventariar, asignar a un capítulo, cotejar.
8. **Un caso clínico en la carpeta de documentos de empresa es una fuga latente.** Moverlo con copia, comparación de hashes y solo después borrar el original.
9. **Las ruedas `.whl` y otros binarios no se versionan.**
10. **Procesar «gratis» un producto no vendido destruye el margen del que sí se vende.** Declarar explícitamente qué entra y qué no en cada contratación.

## Los DAG de la empresa se ven en canvas (omisión corregida 2026-10-12)
La skill instalaba nodos en el DAG pero ningún mapa: el usuario esperaba lienzos como en `wiki-de-proyecto`. Regla: todo frente nuevo del DAG
lleva su vista en `docs/wiki/generar_vistas_dag.py` (`VISTAS`) y su entrada en `wiki.json`; se publica con `publicar.py`.
Vistas mínimas: negocio (fase BP), sistemas (fase SI, catálogo con `fase` propia), primer cliente (fase C). Mientras `instalar.py` no las
añada solo, se agregan a mano al instalar, y `publicar.py` archiva la versión anterior.

## Lecciones de la ejecución del plan (2026-10-12)

11. **El documento oficial gana a la nota derivada, y se pide pronto.** Copia literal del registro y ficha tributaria corrigieron denominación, domicilio fiscal vs estatutario, capital y reparto de socios que las notas daban por «confirmados». Pedirlos al empezar (capítulo de inventario), no al final.
12. **Dependencias de un repo hermano no deben bloquear un capítulo que sólo lo describe.** El estudio técnico dependía de que dos pipelines cerraran su release y arrastraba a toda la cadena (modelo, viabilidad, dossier). Los nodos `externo` cuelgan sólo de lo que de verdad los necesita (la corrida con público), no de los capítulos que los describen.
13. **Los datos abiertos entran con catálogo, licencia, fecha y sha256, antes de los análisis.** Cifras tecleadas con «fuente: resumen de búsqueda» se verificaron contra el PDF descargado; salió igual, pero sólo así se sabe. Plantilla `cargar_abiertos.py`: lector por fuente, falla si cambia el formato, idempotente (la API del BCRP mezcla «Set» y «Sep»).
14. **Ingerir documentos nuevos es comparar por nombre contra el índice y por hash sólo lo dudoso.** Hashear toda la base en un disco montado tardó más de dos minutos y no terminó; el índice con sha256 ya contiene la respuesta.
15. **Lo clínico que llega en una carpeta de empresa ya estaba en su caso.** Comprobar antes de copiar; no duplicar.
16. **El validador externo (abogado, contador) va al final y nada depende de él.** Un nodo de validación terminal (`VAL`); el resto del plan redacta una posición propia y marca ⚠️ lo que sólo ese tercero confirma.
17. **Un PDF escaneado se lee renderizando la página, no con `pdftotext`.** Las páginas 2–4 de la copia literal eran imágenes; a 220 ppi recortadas se leyó el estatuto.
18. **Un número de partida o RUC dispara la alarma de DNI de 8 dígitos.** Se escribe con espacios («16 073 179») en los documentos de git.
19. **Subagentes que redactan en paralelo:** uno por cadena de nodos sin dependencias entre sí; no tocan plan/ ni registro/; el padre verifica contra el texto, corre auditor y tests, hace el commit y registra con el sha.

## Lecciones de cierre y de validación externa (2026-10-13)

20. **Los paquetes para abogado y contador se generan del documento de validación, no se redactan.** `plantillas/validacion/generar_paquetes.py`
    filtra por clase (A / C / AC), quita rutas y nombres de código (lo interno no viaja), añade la tabla de respuestas por rol y copia sólo los
    anexos autorizados. Una prueba exige que lo commiteado coincida con lo generado. Cada paquete lleva un resumen de proceso de una página
    (qué hace la empresa, qué no, quién decide) y marca toda cita normativa «sin cotejo» hasta que el profesional la confirme.
21. **Ensayo no es caso real.** Un piloto hecho con datos ficticios se cierra como «ensayo» y se dice en su título; un experimento cuya propia
    tabla de desenlaces exige n≥k se declara «inconcluso» si n<k. Cerrar con éxito trivial invalida la revisión de lanzamiento que depende de él.
22. **Los mapas se comprueban contra su generador.** Una prueba regenera los lienzos y falla si el publicado difiere; se regenera y publica
    en cada cierre de nodo. Un `ESTADO.md` verde no basta si `plan.json` no se regeneró tras editar `construir_dag.py`.
23. **`construir_dag.py` se edita por bloque de nodo** (regex sobre `n("ID", … )`), nunca por cortes entre nodos no adyacentes: un corte borró
    nodos sin que ninguna compuerta lo notara. Después: regenerar `plan.json` y comprobar el recuento de nodos.
24. **El almacén de datos admite la hoja del plan y los estados `juzgado`/`pausado`.** El CHECK del código de nodo acepta el id corto y el de la
    hoja de release (`REL-…`), y el de estado la lista completa del DAG; si no, el ETL rechaza el propio plan. Con una prueba hostil que lo cubra.
25. **Mecanismo de caja en el almacén:** movimientos (`erp_caja_mov`) con vistas de control: pagos sin doble aprobación, IGV sin separar, caja
    vigente. Las cifras del puente a finanzas salen de un bloque generado, no tecleadas.
26. **Pedidos con orden de fechas verificado y referencias (`--refs`);** la medición de disco recibe la fecha por argumento (sin reloj), y el
    script R se ancla al archivo (no al directorio de trabajo).
27. **Revisión adversarial de lanzamiento (R1):** hallazgos → verificados contra el texto → incidencias → documentos. Los que no pueden
    cerrarse quedan como incidencias abiertas con dueño, no se maquillan.
28. **Un reinicio puede corromper objetos de git:** cuarentena, no borrado; y las corridas largas se reanudan, no se repiten.
