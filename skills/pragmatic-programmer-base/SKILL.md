---
name: pragmatic-programmer-base
description: Meta-principios de artesanía de software extraídos de "The Pragmatic Programmer" (Hunt & Thomas) — DRY de conocimiento (no de texto), ortogonalidad, tracer bullets, diseño por contrato, ventanas rotas, reversibilidad, estimación por rangos. Cargar al diseñar arquitectura, al decidir si algo necesita abstracción/flexibilidad, o al estimar una tarea.
metadata:
  origen: "F:\\skills\\Programacion y matematicas\\pragmatic-programmer-1.0.0"
  extraido: 2026-09-05
  nota: "Nombrado -base para no chocar con la skill global 'pragmatic-programmer' ya instalada en este entorno (versión adaptada a ELEMENT/TGDE). Esta es la versión genérica de la librería F:\\skills, sin esa capa de dominio."
---

# The Pragmatic Programmer — meta-principios

> ⚠️ Este entorno ya tiene instalada una skill global llamada `pragmatic-programmer`
> (con adaptación al dominio ELEMENT/TGDE y un score de madurez medido). Esta skill
> local, `pragmatic-programmer-base`, es la versión genérica de la librería
> `F:\skills\Programacion y matematicas` — úsala cuando la pregunta es de
> arquitectura de software en general, no del dominio bio-predictivo.

## 1. DRY es sobre conocimiento, no sobre texto

Cada pieza de **conocimiento** (una regla de negocio, un valor de
configuración) debe tener una única representación autoritativa. **Dos bloques
de código textualmente idénticos que sirven a reglas de negocio distintas NO
son duplicación** — DRY-earlos crea acoplamiento entre conceptos que en
realidad son independientes y cambian por razones distintas.

Los comentarios que repiten lo que el código ya dice también violan DRY — un
comentario explica el *por qué*, no el *qué*.

## 2. Ortogonalidad

Dos componentes son ortogonales si un cambio en uno no afecta al otro.
**Prueba práctica**: si cambio radicalmente los requisitos detrás de una
función, ¿a cuántos módulos afecta? La respuesta debería ser uno. Evitar el
estado global — cada consumidor de estado global queda acoplado a él.

## 3. Tracer bullets ≠ prototipo

- **Tracer bullet**: un camino delgado pero completo por todo el sistema
  (UI → API → DB). Es código de producción, delgado pero real — **se queda**.
- **Prototipo**: exploración enfocada de un solo aspecto riesgoso — **se
  descarta**, y hay que dejarlo etiquetado como descartable para que no se
  cuele a producción por accidente.

Usar tracer bullets cuando los requisitos son vagos o la arquitectura no está
probada: dan feedback end-to-end antes de invertir en llenar cada feature.

## 4. Diseño por contrato / programación asertiva

- **Precondición**: responsabilidad de quien llama ("acepto solo enteros
  positivos").
- **Postcondición**: garantía de la rutina ("devuelvo una lista ordenada").
- **Invariante**: siempre verdadero ("el balance nunca es negativo").

**Fallar rápido y ruidoso**: un programa muerto hace mucho menos daño que uno
que sigue corriendo en un estado inválido. Usar aserciones para lo que nunca
debería pasar; manejo de errores para lo que podría pasar.

## 5. Ventanas rotas (broken windows)

Un solo hack "lo arreglamos después" empieza el deterioro — una vez que el
sistema muestra descuido, el umbral para agregar más desorden baja a cero. Si
no se puede arreglar ahora, **taparlo explícitamente**: TODO con ticket
asociado, feature deshabilitada, stub documentado — nunca dejarlo silencioso.
El primer hack es el más caro porque da permiso para todos los siguientes.

## 6. Reversibilidad

No hay decisiones finales. Abstraer las dependencias de terceros detrás de
interfaces propias — nunca dejar que una API de proveedor se filtre a la
lógica de negocio. **Prueba del camino bifurcado**: ¿se podría cambiar de
Postgres a DynamoDB en una semana? Si no, hay acoplamiento oculto.

YAGNI también aplica a la flexibilidad: no construir abstracción "por si
acaso" sin evidencia concreta de que hará falta.

## 7. Estimación honesta y portafolio de conocimiento

- Un rango con nivel de confianza ("3–5 días") es más honesto y más útil que
  un número exacto que erosiona confianza cuando falla.
- PERT: `(Optimista + 4×Más probable + Pesimista) / 6`.
- Descomponer en componentes y estimar cada uno — la suma es más precisa que
  una sola adivinanza.
- Mantener un knowledge portfolio: invertir tiempo regularmente en aprender
  algo nuevo, diversificar más allá del stack actual.

## Errores comunes y su arreglo

| Error | Por qué falla | Arreglo |
|---|---|---|
| DRY-ear código parecido que sirve propósitos distintos | Acopla conceptos no relacionados | Solo DRY-ear conocimiento, no similitud textual coincidente |
| Saltarse el tracer bullet y construir capa por capa | Los problemas de integración aparecen tarde | Construir primero una rebanada vertical delgada |
| Ignorar ventanas rotas "las arreglamos después" | La entropía se acelera; "después" nunca llega | Arreglar ya o tapar con un ticket rastreado |
| Estimaciones como compromiso puntual | Falsa precisión, erosiona confianza | Dar siempre rangos con nivel de confianza |
| Hacer todo "flexible" de entrada | Sobre-ingeniería sin evidencia de necesidad | Agregar flexibilidad solo con evidencia concreta |
| Quitar aserciones "por rendimiento" | Bugs que las aserciones detectarían corrompen datos en silencio | Mantener las aserciones críticas; medir antes de sacarlas |

## Diagnóstico rápido

- ¿Puedo cambiar la base de datos sin tocar la lógica de negocio? (si no → falta ortogonalidad)
- ¿Tengo una rebanada end-to-end funcionando? (si no → falta tracer bullet)
- ¿Cada regla de negocio está definida en exactamente un lugar? (si no → violación DRY)
- ¿Mis estimaciones incluyen rango y confianza? (si no → cambiar a PERT/rango)
- ¿Puedo revertir este deploy en menos de 5 minutos? (si no → falta reversibilidad)
