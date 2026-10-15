---
name: functional-immutability
description: Reglas de programación funcional e inmutabilidad — funciones puras, composición, ADTs, cuándo NO usar FP, closures vs objetos. Cargar al diseñar transformaciones de datos/pipelines, al decidir entre mutar o transformar, al elegir entre POO y FP para un módulo, o al revisar código con efectos secundarios ocultos.
metadata:
  origen: "F:\\skills\\Programacion y matematicas\\Functional-programmer-inmutabilty"
  extraido: 2026-09-05
---

# Programación funcional e inmutabilidad

## Los cuatro pilares

1. **Inmutabilidad hace el tiempo explícito.** Las estructuras no se modifican
   in place; las transformaciones producen estructuras nuevas. Esto elimina
   toda una clase de bugs (mutaciones inesperadas, condiciones de carrera) y
   permite compartir datos sin copia defensiva.
2. **Funciones puras habilitan el razonamiento.** Misma entrada → misma
   salida, sin efectos secundarios. Permiten testear sin setup complejo,
   componer libremente, paralelizar sin miedo, y cachear (memoización).
3. **Funciones de orden superior como abstracción.** Abstraer sobre patrones
   (map/filter/reduce), no solo sobre datos.
4. **Estilo declarativo expresa intención.** Decir *qué* computar, no *cómo* —
   el código se lee como especificación.

## Regla de oro: empujar los efectos a los bordes

Los programas reales necesitan I/O y estado. La estrategia no es eliminar los
efectos sino **empujarlos al borde del programa** y mantener el núcleo de
lógica de negocio puro. Estrategias concretas: paso explícito de estado por
parámetros, inyección de dependencias para el contexto (reloj, almacenamiento,
generador de IDs), o un wrapper de efectos en el borde (adapter/gateway).

## ADTs para hacer imposibles los estados inválidos

Usar sum types (variantes) y product types (records) para que el compilador
(o el linter/tipo) atrape casos faltantes en un pattern match, elimine chequeos
de null (`Option`/`Maybe`), y modele máquinas de estado explícitamente.

## Cuándo NO usar programación funcional

No forzar FP como dogma. Evitarla quirúrgicamente en:

- **Loops calientes de rendimiento crítico**: la inmutabilidad y las
  estructuras persistentes tienen overhead; mutar en el lugar puede ser
  órdenes de magnitud más rápido — perfilar antes de descartar FP, no asumir.
- **Dominios inherentemente statefuls**: UIs con estado local complejo, game
  loops, simulaciones con actualización in-place — considerar imperativo/OOP.
- **Equipo/ecosistema no familiarizado con FP**: el costo de entrenamiento
  puede superar el beneficio si el resto del código base es imperativo.

## Closures y objetos son equivalentes

Ambos son mecanismos para encapsular estado con comportamiento — la
diferencia es sintaxis y convención, no poder expresivo. Elegir según el
idioma del lenguaje/codebase, no por dogma.

## Trade-offs de recursión

Preferir recursión para árboles/grafos, divide-and-conquer, estructuras
recursivas por definición. Usar iteración cuando el lenguaje no optimiza tail
calls (riesgo de stack overflow) o cuando la iteración es simplemente más
clara — medir antes de asumir que la recursión es más lenta.

## Monads: usar con criterio, no reflejo

`Option`/`Result`/`IO` resuelven problemas concretos (ausencia explícita,
manejo de error como valor, aislar efectos). No forzarlos si el lenguaje ya
tiene un idiom más simple (excepciones aceptadas, null-checks triviales) o si
el equipo no está familiarizado — la abstracción debe aclarar, no oscurecer.

## Errores comunes al venir de OOP/imperativo

| Origen | Error típico | Arreglo |
|---|---|---|
| OOP | Crear jerarquías de closures imitando herencia | Datos + funciones; no todo necesita encapsulación tipo objeto |
| OOP | Patrones `Manager`/`Helper` (bundles de closures disfrazados) | Componer funciones simples; un Manager suele indicar abstracción faltante |
| OOP | Copia defensiva en vez de estructuras persistentes | Usar structural sharing del lenguaje; transformar, no copiar |
| Imperativo | Traducir loops línea por línea con `let` que hacen shadow | Expresar como transformación de datos (map/filter/reduce) o recursión |
| Imperativo | Pipelines secuenciales cuando las operaciones son independientes | Reconocer paralelismo — las funciones puras lo habilitan de forma segura |
| Imperativo | "Solo una variable mutable, por eficiencia" | Empezar puro; optimizar solo tras perfilar. La mutación es contagiosa |

## Otros pitfalls a vigilar

- **Estilo pointfree excesivo**: usarlo para composiciones simples; agregar
  parámetros explícitos cuando mejora la claridad.
- **Abstracción prematura**: abstraer recién al ver el patrón repetirse 3+
  veces — dejar que la abstracción emerja del código concreto.
- **Ignorar el modelo de evaluación del lenguaje** (estricto vs. lazy):
  Haskell evalúa lazy (riesgo de space leaks); la mayoría de lenguajes son
  estrictos (predecibles pero evalúan todo).
