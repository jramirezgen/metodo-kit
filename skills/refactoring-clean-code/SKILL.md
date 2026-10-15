---
name: refactoring-clean-code
description: Reglas y umbrales objetivos para refactorizar código tangled — catálogo de code smells, violaciones SOLID con ejemplo de arreglo, umbrales de complejidad/tamaño, y cómo priorizar deuda técnica. Cargar al revisar código difícil de mantener, antes de un refactor grande, o al decidir si vale la pena pagar deuda técnica ahora.
metadata:
  origen: "F:\\skills\\Programacion y matematicas\\code-refactoring-refactor-clean-1.0.0"
  extraido: 2026-09-05
---

# Refactor y clean code

## Cuándo aplica

Código tangled o difícil de mantener, reducir duplicación/complejidad/code
smells, mejorar testabilidad, preparar un módulo para una feature nueva sin
romperlo.

**No aplica** a un fix de una línea, código bajo change-freeze, o cuando lo
pedido es solo documentación.

## Regla de seguridad primero

- No cambiar comportamiento externo sin aprobación explícita.
- Aplicar cambios en slices pequeños y mantener los tests en verde entre cada
  paso.
- Actualizar tests junto con el refactor; verificar que no hay regresiones.

## Catálogo de code smells a buscar

- Métodos/funciones largos (>20 líneas), clases grandes (>200 líneas).
- Bloques de código duplicados; código muerto y variables sin usar.
- Condicionales complejos y loops anidados (>2 niveles).
- Números mágicos y valores hardcodeados.
- Nombres poco descriptivos; acoplamiento fuerte entre componentes.
- **Long Parameter List** → extraer un Parameter Object.
- **Feature Envy** (un método usa más los datos de otra clase que los propios)
  → mover el método a la clase de la que depende.
- **Obsesión primitiva** (`string` para email, `number` para dinero) → value
  object con validación en el constructor.

## Umbrales objetivos (no de sentido común, son gate)

| Métrica | Bien | Alerta | Crítico → acción |
|---|---|---|---|
| Complejidad ciclomática | <10 | 10–15 | >15 → partir en métodos más chicos |
| Líneas por método | <20 | 20–50 | >50 → extraer métodos, aplicar SRP |
| Líneas por clase | <200 | 200–500 | >500 → descomponer en varias clases |
| Cobertura de tests | >80% | 60–80% | <60% → agregar tests unitarios ya |
| Duplicación de código | <3% | 3–5% | >5% → extraer código común |
| Parámetros por función | ≤3 | — | >3 → Parameter Object |

## SOLID: el arreglo concreto, no solo el nombre

- **SRP violado** → una clase con un solo método público por responsabilidad,
  inyectadas por composición (`UserValidator`, `UserRepository`,
  `EmailService`, `UserActivityLogger` en vez de un `UserManager` que hace
  todo).
- **OCP violado** (un `if/elif` por cada variante) → Strategy pattern: una
  interfaz `DiscountStrategy` con una implementación por variante; agregar una
  variante nueva no toca el código existente.
- **LSP violado** (`Square extends Rectangle` rompe `setWidth`/`setHeight`) →
  no heredar cuando el subtipo cambia el contrato; usar una interfaz común
  (`Shape.area()`) sin relación de herencia forzada.
- **ISP violado** (interfaz gorda que fuerza métodos que no aplican, ej.
  `Robot implements Worker{work,eat,sleep}`) → partir en interfaces de rol
  (`Workable`, `Eatable`, `Sleepable`).
- **DIP violado** (`UserService` instancia `MySQLDatabase` directamente) →
  ambos dependen de una interfaz `Database`; la clase concreta se inyecta
  desde afuera (`NewUserService(db Database)`).

## Cómo priorizar qué refactorizar primero

```
¿Causa bugs en producción?        → CRÍTICO, arreglar ya
¿Bloquea features nuevas?         → ALTO, agendar este sprint
¿Se modifica con frecuencia?      → MEDIO, próximo trimestre
¿Cobertura de tests < 60%?        → MEDIO, agregar tests
Ninguno de los anteriores         → BAJO, backlog
```

Fórmula de referencia:
`Prioridad = (Valor de negocio × Deuda técnica) / (Esfuerzo × Riesgo)`

## Checklist de salida de un refactor

- [ ] Ningún método supera ~20 líneas ni ninguna clase ~200 líneas sin justificación.
- [ ] Ninguna función tiene más de 3 parámetros sin Parameter Object.
- [ ] Complejidad ciclomática < 10.
- [ ] Nombres descriptivos, sin abreviaturas crípticas.
- [ ] Sin código comentado ("por si acaso").
- [ ] Manejo de errores con excepciones específicas, no genéricas.
- [ ] Tests cubren el comportamiento refactorizado y siguen en verde.
- [ ] Ningún secreto hardcodeado quedó expuesto por el refactor.
