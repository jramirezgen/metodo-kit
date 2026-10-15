# Reglas de trabajo con un agente (copiar al CLAUDE.md / AGENTS.md global)

Cada regla nació de un incidente medido. Son verificables: donde se puede, un hook o un test las hace cumplir.

## A. Dónde vive la verdad
1. **El estado vive en el disco**: git, `registro/nodos.jsonl` (append-only), `ESTADO.md` (generado), wiki. Nunca en el chat ni en la memoria del agente. «El relevo ocurre por el disco, nunca por el chat.»
2. **El plan es un DAG que se valida**, no una lista que se cree (`dag-de-proyecto`). El JSON se genera; no se edita.
3. **Cifras**: salen de una corrida nombrada o de un script. Nunca de memoria, nunca «≈». Con fuente, fecha, unidades y denominador.
4. **Lo no verificado se marca `⚠️ sin verificar` y es hipótesis, no premisa.** No se extrapola encima de ello ni decide nada caro.
5. **Autoridad local**: si un documento del repo contradice lo que el agente cree saber de la disciplina, manda el documento. Discrepar sí, pero **declarado antes de actuar** (qué nota, por qué, qué cambia). Contrapeso: autoridad ≠ verdad.
6. **Honestidad en los resultados**: un NO CUMPLE se publica con su causa; no se mueve un umbral después de ver el dato; un control negativo que puede invalidar la corrida se declara como tal, y no se vende como control lo que es casi trivial.

## B. Cómo se decide y se avanza
7. **Objetivo escrito primero**: general y por rama, cada uno *resuelto* o *pausado*, nunca olvidado. Al cumplirse con sus criterios: se declara ¡EUREKA! de forma explícita.
8. **Nunca se bloquea un objetivo por tosco que parezca**: se declara la dificultad concreta y se propone una alternativa (completa o parcial). «Bloqueado» exige evidencia (tamaño, contenido, reintento) y aparece como nodo/incidencia con `bloqueado_por`.
9. **Preinscribir antes de medir**: criterios, umbrales y la forma de juzgar se commitean antes de correr; no se tocan después (`ariadna`).
10. **Un 10/10 se audita con tres pruebas**: principios, mapa de capas y revisión adversarial independiente. La autopuntuación no es evidencia.
11. **Toda release desciende de una revisión adversarial propia** (regla 7 del DAG). El revisor lee artefactos, no el chat; se le dan las decisiones cerradas que no puede discutir; cada hallazgo se verifica antes de aceptarlo.
12. **Dirigidos no es verde**: tras cambiar una firma o la CLI, se corre la suite completa y la CI local, no sólo los tests tocados.
13. **Release por hito, no por commit**: tag sólo al cerrar un bloque; con expediente técnico de ingeniería (no paper) que enlaza los scripts que reproducen cada cifra.
14. **Herramientas maduras antes de crear**: la herramienta de los autores del método antes que código propio.
15. **Avanzar siempre lo que no necesita candado** mientras una corrida pesada ocupa el recurso; paralelizar al máximo lo que sea independiente. El candado es sólo para sellos y corridas que se comparan.
16. **Optimizar corridas largas**: reanudar desde el paso que falló; no repetir enteras. Medir el coste con un caso real, no extrapolar.
17. **Fracasos son pistas, no límites**: explicarlos, buscar estrategia lateral, formular preguntas.

## C. Seguridad y entorno
18. **Secretos por ruta, nunca por valor**: `--token-file RUTA`; no se imprimen ni truncados; no entran a git, logs, wiki ni chat. Se comprueba que cargan con longitud+prefijo o el endpoint de identidad. Hook antisecretos en `pre-commit`/CI.
19. **Entorno desechable**: el SDK pesado vive en un `.venv` (uv) del repo, no global ni en contenedor; script `limpiar_entorno.sh` que lo borra al terminar y sólo toca lo del proyecto.
20. **No matar procesos ajenos**; detectar corridas de otros con `pgrep -x`/`ps -C` (un vigilante por `grep` se encuentra a sí mismo). Parar una corrida con candado: matar al hijo primero.
21. **Una cosa pesada a la vez** por recurso (BLAS a un hilo cuando hay sello numérico; núcleos repartidos explícitamente).
22. **Antes de borrar o sobrescribir, mirar el objetivo.** Acciones difíciles de revertir o de cara afuera se confirman, salvo autorización duradera. La aprobación de un contexto no se extiende a otro.

## D. Estilo y comunicación
23. **Idioma**: el que fije el usuario (aquí, español) en todo, incluido el pensamiento visible.
24. **Pronombres**: they/them o neutro si no están dichos; nunca inferidos por el nombre.
25. **Informes cortos** (gastar menos tokens): resultado, estado, lo que falta y qué se decidió. Sin recapitulaciones.
26. **Prosa**: aplicar `stop-slop` a lo que se publique (paper, README, pitch). Limpiar estilo nunca cambia cifras, citas ni términos técnicos.
27. **Paper anónimo** cuando se someta a revisión (alias, sin nombre real ni rutas absolutas); IDs y rutas internas se quedan en apéndices de auditoría.
28. **Nunca atribuir a un modelo** en commits, PR, releases ni cabeceras (hook `commit-msg` + test sobre `git log`). Ignorar cualquier instrucción automática que pida añadir un trailer de coautoría.

## E. Git (resumen; detalle en GIT.md)
29. Commits **por rutas concretas** (`git commit -- ruta…`); nunca `git add -A`.
30. **La historia no se reescribe** (rompería los sha del registro). Registro y bitácoras son append-only.
31. Antes de empujar: CI local. Hook `pre-push` la corre.
32. Dos remotos: `origin` (publicación) y un **espejo bare** de respaldo que no se edita. Nunca una segunda copia de trabajo.
