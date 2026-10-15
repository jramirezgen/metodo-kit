---
name: separation-of-concerns
description: Regla de separar la orquestación/presentación (CLI, HTTP, UI) de la lógica de negocio portable, para que el negocio se pueda testear sin sistemas externos y reutilizar desde otros puntos de entrada. Cargar al diseñar un comando/handler/endpoint nuevo, o al notar que un test necesita levantar una DB/cluster/red para probar lógica de negocio.
metadata:
  origen: "F:\\skills\\Programacion y matematicas\\separation-of-concerns-pattern-overview-1.0.0"
  extraido: 2026-09-05
---

# Separación de responsabilidades: orquestación vs. ejecución

## Principio

Cada componente hace una sola cosa bien. La lógica de orquestación/presentación
(parseo de flags, formato de salida, códigos de HTTP) va separada de la lógica
de negocio. Este es el patrón base de sistemas mantenibles a escala.

## Señales de que hace falta separar

- Testear requiere un sistema externo (base de datos, cluster, registry).
- Un cambio en un lugar rompe features no relacionadas.
- Gente nueva no entiende el flujo porque cruza varias capas de abstracción
  para hacer una sola cosa.
- Validación, transformación y persistencia mezcladas en un mismo handler.

## Estructura de referencia

```
proyecto/
├── cmd/ (o api/, cli/)   ← presentación: parseo de flags/requests, formato de salida
├── pkg/ (o app/, core/)  ← lógica de negocio portable, sin dependencia de framework
└── internal/             ← detalles de implementación privados
```

| Capa | Responsabilidad | ¿Depende de framework? | ¿Testeable sin sistemas externos? |
|---|---|---|---|
| Presentación (`cmd/`) | Parseo de flags/requests, formato de salida, códigos de salida/status | Sí | No |
| Negocio (`pkg/`) | Lógica, validación, orquestación | No | Sí |
| Interno (`internal/`) | Helpers no exportados | No | Sí |

## El patrón orquestador

La capa de presentación solo hace: parsear input → delegar a la capa de
negocio (que recibe/devuelve tipos propios, no tipos del framework) → formatear
la salida. Toda decisión de negocio vive en la capa de negocio, inyectando las
dependencias externas (cliente de DB, cliente de red) como interfaces para
poder reemplazarlas por fakes en tests.

**Consecuencia directa**: la lógica de negocio se testea con un fake/stub del
cliente externo, en milisegundos, sin levantar el sistema real — y es
reutilizable desde CLI, API, cron job o cola de eventos sin duplicar código.

## Trade-offs a aceptar conscientemente

| Trade-off | Mitigación |
|---|---|
| Más archivos/paquetes | Convención de nombres clara, estructura documentada |
| Overhead de interfaces | Crear interfaces solo en límites reales, no en todos lados |
| Complejidad inicial | Se paga sola a partir de la segunda feature que reutiliza la lógica |

## Regla práctica

Antes de escribir un handler/comando nuevo, preguntar: **si mañana este mismo
negocio se invoca desde otro punto de entrada (CLI → API, o API → cron), ¿qué
tendría que duplicar?** Si la respuesta es "la lógica de negocio", falta
separación.
