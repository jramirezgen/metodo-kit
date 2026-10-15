---
name: domain-driven-design
description: Reglas de modelado de dominio (DDD + diseño orientado a datos de Rich Hickey + diseño orientado a tipos de Scott Wlaschin) — entidades vs value objects, agregados, bounded contexts, lenguaje ubicuo, hacer los estados ilegales irrepresentables. Cargar al modelar un dominio nuevo, al diseñar tipos/esquemas, al nombrar conceptos de negocio, o al revisar si un modelo tiene inconsistencias.
metadata:
  origen: "F:\\skills\\Programacion y matematicas\\Domain-drive-design"
  extraido: 2026-09-05
---

# Modelado de dominio (DDD orientado a datos y a tipos)

> Síntesis de la skill local de DDD, que combina Eric Evans (DDD clásico), Rich
> Hickey (diseño orientado a datos) y Scott Wlaschin (diseño orientado a tipos).

## Principio rector: hacer los estados ilegales irrepresentables

Usar el sistema de tipos para que un estado inválido **no se pueda construir**,
en vez de validarlo después. Preferir sum types/discriminated unions sobre
combinaciones de booleanos u opcionales sueltos.

```
// Mal: dos campos opcionales que pueden estar ambos seteados
{ status: "approved" | "rejected", approvedAt?: Date, rejectedAt?: Date }

// Bien: un solo tipo que hace imposible el estado contradictorio
type PaymentStatus =
  | { kind: "Pending" }
  | { kind: "Approved", approvedAt: Timestamp, approvedBy: UserId }
  | { kind: "Rejected", rejectedAt: Timestamp, reason: string }
```

## Reglas duras (Rich Hickey — datos primero)

- **Los datos son el rey**: modelar el dominio con estructuras de datos simples
  (mapas, listas, records), no con objetos que envuelven comportamiento. Las
  funciones transforman datos; los datos no ejecutan comportamiento.
- **Simplicidad ≠ facilidad**: preferir construcciones simples que se entiendan
  de forma independiente sobre las que son fáciles de escribir pero entrelazan
  (complect) conceptos no relacionados.
- **Decomplecting**: separar siempre "cuándo pasa algo" de "qué pasa", y
  "mecanismo" de "política". Preguntar: ¿estos dos conceptos son realmente
  distintos, o los enredamos sin darnos cuenta?
- **Valor de los valores**: los hechos del dominio se representan con valores
  inmutables — se pueden compartir sin coordinación y comparar por igualdad
  estructural.

## Reglas duras (Wlaschin — tipos primero)

- **Modelar el workflow como transformación de datos**: `Input → Proceso →
  Output`, con las reglas de negocio como funciones explícitas.
- **Railway-oriented programming**: modelar éxito y fallo como caminos
  explícitos (`Result`/`Either`), encadenados con bind/flatMap, manteniendo el
  camino feliz lineal y legible.
- **Wrappers semánticos sobre primitivos**: nunca un `string` para email o un
  `number` para dinero sin envolver — `EmailAddress`, `Money { amount, currency }`.
- **Los tipos documentan intención**: la firma de una función debe comunicar
  qué hace sin necesidad de leer el cuerpo.

## Entidad vs Value Object — cómo decidir

- ¿Los expertos del dominio se refieren a esto por ID/nombre? → **Entidad**
  (identidad propia, puede cambiar de atributos manteniendo identidad).
- ¿Se puede reemplazar por una copia equivalente sin que importe? → **Value
  Object** (inmutable, sin identidad, dos VOs iguales son intercambiables).

## Agregados

- El **Aggregate Root** es el único punto de entrada externo al agregado;
  referencias externas usan solo su ID.
- El root aplica todos los invariantes del agregado completo.
- Las transacciones no cruzan límites de agregado — entre agregados, usar
  consistencia eventual.
- Mantener los agregados pequeños. **No crear un agregado** si los objetos se
  modifican de forma independiente y no comparten invariantes transaccionales.

## Bounded contexts y lenguaje ubicuo

- El lenguaje ubicuo **es ubicuo solo dentro de un contexto**: "Cliente" en
  Ventas puede no ser lo mismo que "Cliente" en Logística — no forzar un
  modelo único cuando el negocio ya distingue los contextos.
- Hacer explícitos los límites de contexto en la estructura del código
  (módulos/paquetes separados), y usar capas anti-corrupción al integrar entre
  contextos.
- Resistir renombrar un concepto de dominio por conveniencia técnica. Los
  nombres de tipos, funciones y módulos deben calcar el vocabulario del
  negocio, no jerga técnica (`Manager`, `Handler`, `Factory` solo si el propio
  negocio usa esas palabras).

## Antipatrones a detectar

| Antipatrón | Síntoma | Arreglo |
|---|---|---|
| Modelo de dominio anémico | Structs con getters/setters, toda la lógica en servicios aparte | Datos como datos; transformaciones relacionadas en el mismo módulo, separadas de la definición del dato |
| Entity Services | `UserService`, `OrderManager`, `ProductFactory` | Nombrar funciones con verbos de dominio: `approveOrder`, `cancelSubscription` |
| Obsesión primitiva | `string` para email, `number` para dinero, flags booleanos para estado | Tipos semánticos con validación en la construcción |
| Ceguera booleana | `isApproved`, `isActive`, `isDeleted` como flags independientes | Sum type para estados mutuamente excluyentes |
| Acoplamiento temporal oculto | Hay que llamar A antes que B o el sistema se rompe | Hacer el workflow explícito; usar tipos que fuercen la transición válida |

## Checklist antes de dar por cerrado un modelo de dominio

- [ ] Los tipos hacen irrepresentables los estados ilegales.
- [ ] Entidades con identidad clara; value objects inmutables.
- [ ] Sum types para estados mutuamente excluyentes (no combinaciones de booleanos/opcionales).
- [ ] Los límites de agregado son explícitos y el root aplica los invariantes.
- [ ] El bounded context está identificado; el término técnico no se filtró al dominio.
- [ ] Terminología idéntica en código, docs y conversación (glosario actualizado).
