# Auditoría de ⟨proyecto⟩ ⟨versión⟩ — deficiencias hacia ⟨versión objetivo⟩

Fecha: ⟨AAAA-MM-DD⟩. **Sólo lectura: no se tocó código.**

**Fuentes:** lectura del código con fichero:línea; ⟨mediciones previas⟩; el tablero de
incidencias (⟨N⟩ abiertas); la suite en ⟨cada entorno⟩: ⟨pasan / fallan / se saltan⟩.

## 0. Lo que cambia el plan

⟨El hallazgo estructural que reordena todo. Suele ser un acoplamiento que nadie había dibujado.⟩

## 1. Lista de deficiencias

Leyenda: **P** bloquea producción · **V** afecta a la validez · **R** robustez · **E** estética.
Coste: S < 1 h · M medio día · L días o depende de fuera.

| id | qué | dónde (fichero:línea) | alcance medido | ruta | incidencia | clase | coste |
|---|---|---|---|---|---|---|---|
| ⟨M1⟩ | ⟨…⟩ | ⟨…⟩ | ⟨recuento⟩ | ⟨…⟩ | ⟨INC-###⟩ | ⟨P/V/R/E⟩ | ⟨S/M/L · por qué⟩ |

## 2. Bloqueos y cómo se sortean

⟨Cada bloqueo con su **alternativa**. Ninguno queda como «no se puede» a secas.⟩

## 3. Incidencias antiguas que piden triaje

⟨Las que son de otro objetivo: se proponen **pausadas**, no obsoletas. Decide el usuario.⟩

## 4. Orden propuesto

⟨Primero lo que no cambia comportamiento (se juzga IDÉNTICO), después lo barato, después lo
que mueve el sello a propósito (con delta esperado), al final integración, robustez y release.⟩
