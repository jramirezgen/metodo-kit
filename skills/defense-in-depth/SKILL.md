---
name: defense-in-depth
description: Regla de validar en cada capa por la que pasa un dato para hacer un bug estructuralmente imposible, no solo corregido en un punto. Cargar al arreglar un bug causado por un dato inválido, al diseñar dónde poner una validación, o al revisar si un solo chequeo es suficiente.
metadata:
  origen: "F:\\skills\\Programacion y matematicas\\defense-in-depth-1.0.0"
  extraido: 2026-09-05
---

# Defensa en profundidad para validación de datos

## Principio

Cuando un bug es causado por un dato inválido, validar en un solo lugar se
siente suficiente — pero ese único chequeo puede ser saltado por otro código
path, por un refactor futuro, o por un mock en un test.

**Regla dura: validar en CADA capa por la que pasa el dato.** El objetivo no
es "arreglamos el bug" sino "hicimos el bug estructuralmente imposible".

## Las cuatro capas

1. **Validación de entrada (entry point)**: rechazar lo obviamente inválido en
   el borde de la API/función pública (`workingDirectory` vacío, ruta que no
   existe, etc.).
2. **Validación de lógica de negocio**: confirmar que el dato tiene sentido
   *para esta operación concreta*, aunque ya haya pasado la validación de
   entrada.
3. **Guardas de entorno**: prevenir operaciones peligrosas en contextos
   específicos (p. ej. rechazar `git init` fuera de un directorio temporal
   cuando `NODE_ENV=test`).
4. **Instrumentación de debug**: loggear contexto (stack trace, cwd, valores)
   justo antes de la operación riesgosa, para cuando las otras tres capas
   fallen igual.

## Por qué las cuatro son necesarias, no redundantes

Cada capa atrapa casos que las otras se saltan:
- Distintos code paths saltean la validación de entrada.
- Los mocks en tests saltean los chequeos de lógica de negocio.
- Edge cases específicos de plataforma necesitan guardas de entorno.
- El logging de debug es lo único que queda cuando todo lo demás fue
  esquivado.

**No parar en el primer punto de validación que "resuelve" el bug.**

## Cómo aplicar el patrón ante un bug

1. Rastrear el flujo del dato: ¿dónde se origina el valor malo? ¿dónde se usa?
2. Mapear todos los checkpoints por los que pasa.
3. Agregar validación en cada capa: entrada, negocio, entorno, debug.
4. Testear cada capa por separado: intentar saltarse la capa 1 y confirmar
   que la capa 2 lo atrapa.
