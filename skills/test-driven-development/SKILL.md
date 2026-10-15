---
name: test-driven-development
description: Reglas de TDD (ciclo rojo-verde-refactor, patrón "pruébalo" para bugs, pirámide de tests, qué mockear y qué no). Cargar antes de implementar lógica nueva, antes de arreglar un bug, o al cambiar comportamiento existente — siempre que el cambio pueda romper algo.
metadata:
  origen: "F:\\skills\\Programacion y matematicas\\Test-Driven-Development"
  extraido: 2026-09-05
---

# TDD: probar antes de implementar

## Cuándo aplica

Implementar lógica/comportamiento nuevo, arreglar cualquier bug, modificar
comportamiento existente, agregar manejo de edge cases: siempre escribir el
test antes o junto con el cambio.

**No aplica** a cambios puros de configuración, documentación o contenido
estático sin impacto de comportamiento.

## El ciclo

```
ROJO                VERDE                 REFACTOR
Escribir un    →   Escribir el código   →   Limpiar la
test que falla     mínimo que lo pasa       implementación  → (repetir)
```

1. **ROJO**: el test se escribe primero y **debe fallar**. Un test que pasa a
   la primera no prueba nada.
2. **VERDE**: código mínimo para pasar el test — no sobre-diseñar en este paso.
3. **REFACTOR**: con los tests en verde, limpiar (extraer, renombrar, quitar
   duplicación) corriendo los tests después de cada paso.

## Patrón "pruébalo" para bugs (Prove-It Pattern)

Ante un reporte de bug, **no arrancar por el fix**. Primero escribir un test
que reproduzca el bug y confirmar que falla; recién ahí implementar el arreglo
y verificar que el test pasa y que el resto de la suite sigue en verde.

## La pirámide de tests

```
        E2E (~5%)            — flujos completos, navegador real
     Integración (~15%)      — interacción entre componentes, límites de API
  Unitarios (~80%)           — lógica pura, aislada, milisegundos
```

**Regla Beyoncé**: si te gustó, le pusiste un test. Un refactor o una
migración no son responsables de atrapar tus bugs — tus tests sí.

### Clasificación por recursos consumidos

| Tamaño | Restricciones | Velocidad |
|---|---|---|
| Pequeño | Un solo proceso, sin I/O, sin red, sin DB | milisegundos |
| Mediano | Multi-proceso OK, solo localhost, sin servicios externos | segundos |
| Grande | Multi-máquina, servicios externos permitidos | minutos |

La mayoría de la suite debe ser "pequeña": rápida, confiable, fácil de
depurar cuando falla.

## Cómo escribir buenos tests

- **Probar estado, no interacciones.** Verificar el resultado de una
  operación, no qué métodos internos se llamaron — un test de interacción se
  rompe al refactorizar aunque el comportamiento no cambie.
- **DAMP sobre DRY en tests.** En código de producción DRY es correcto casi
  siempre; en tests, cada caso debe leerse como una historia completa sin
  necesidad de rastrear helpers compartidos. La duplicación en tests es
  aceptable si hace que cada test se entienda solo.
- **Preferir implementaciones reales sobre mocks**, en este orden de
  preferencia: real > fake (versión en memoria) > stub (datos enlatados) >
  mock de interacción (verifica llamadas — usar con moderación). Mockear solo
  cuando lo real es lento, no determinista, o tiene efectos incontrolables
  (APIs externas, envío de emails).
- **Arrange-Act-Assert** como estructura de cada test.
- **Una aserción por concepto** — varios tests pequeños en vez de uno que
  verifica todo.
- **Nombrar tests como especificación**: `it('sets completedAt when task is
  completed')`, nunca `it('works')`.

## Antipatrones de testing

| Antipatrón | Problema | Arreglo |
|---|---|---|
| Testear detalles de implementación | Se rompe al refactorizar aunque el comportamiento no cambió | Probar inputs/outputs, no estructura interna |
| Tests flaky (timing, dependientes de orden) | Erosionan la confianza en la suite | Aserciones deterministas, aislar el estado de cada test |
| Testear código de framework | Desperdicia tiempo probando comportamiento de terceros | Solo probar código propio |
| Abuso de snapshots | Snapshots enormes que nadie revisa, se rompen con cualquier cambio | Usar snapshots con moderación y revisar cada diff |
| Falta de aislamiento entre tests | Pasan individualmente, fallan juntos | Cada test monta y desmonta su propio estado |
| Mockear todo | Los tests pasan pero producción se rompe | Preferir real > fake > stub > mock; mockear solo en los bordes |

## Verificación antes de dar por cerrado un cambio

- [ ] Todo comportamiento nuevo tiene un test correspondiente.
- [ ] Todos los tests pasan.
- [ ] Los arreglos de bugs incluyen un test de reproducción que fallaba antes del fix.
- [ ] Los nombres de los tests describen el comportamiento verificado.
- [ ] Ningún test fue saltado o deshabilitado para que la suite pase.
- [ ] No repetir el mismo comando de test sin haber cambiado código de por medio — no aporta confianza extra.
