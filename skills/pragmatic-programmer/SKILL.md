---
name: pragmatic-programmer
description: "LEER PRIMERO, ANTES de escribir o modificar cualquier código, y antes de proponer una arquitectura o un refactor. Meta-principios de artesanía de software: DRY, ortogonalidad, balas trazadoras, diseño por contrato, ventanas rotas, reversibilidad y estimación. Úsalo al escribir código nuevo, al tocar código existente, al revisar arquitectura, al decidir cómo atacar deuda técnica, al estimar, o al preguntarse qué haría un ingeniero pragmático. Incluye la adaptación al dominio ELEMENT/TGDE (bio-diseño predictivo) con su score de madurez medido."
license: MIT
metadata:
  author: wondelai
  version: 2.0.0
  mcpmarket-version: 1.0.0
  adaptado-por: "Kaitokid — references/element-tgde.md, score ELEMENT 8.7/10 (2026-07-18)"
  adelgazado: "2026-07-28 — divulgación progresiva: ~4 700 → ~1 200 tokens por invocación, sin perder contenido (ver references/principios-detalle.md)"
---

# The Pragmatic Programmer

**Cuida tu oficio.** No basta con que el código funcione: tiene que ser fácil de
cambiar, de entender y de merecer confianza. Estos siete principios son el
meta-nivel —cómo pensar sobre el software— y se aplican antes de la primera línea.

> Este fichero es corto **a propósito**: se carga en cada invocación. El detalle
> vive en `references/` y se abre solo cuando hace falta.

## Los siete principios

| # | Principio | En una línea | Cuándo muerde |
| --- | --- | --- | --- |
| 1 | **DRY** | Cada pieza de **conocimiento** tiene una representación única y autoritativa | Cambias una regla, hay que tocarla en tres sitios, y uno se olvida |
| 2 | **Ortogonalidad** | Cambiar un componente no debe afectar a otro | Tocas la base de datos y se rompe la interfaz |
| 3 | **Balas trazadoras** | Una rebanada vertical fina pero **real**, de punta a punta, antes de rellenar | Construyes capa por capa y la integración falla al final |
| 4 | **Diseño por contrato** | Precondiciones, postcondiciones e invariantes — y fallar rápido y ruidoso | El programa sigue vivo en estado inválido y corrompe datos en silencio |
| 5 | **Ventanas rotas** | Un desperfecto sin arreglar da permiso a todos los siguientes | "Ya lo arreglaremos" y la entropía se acelera |
| 6 | **Reversibilidad** | No hay decisiones finales; el coste del cambio debe ser proporcional a su alcance | El proveedor cambia y migrar es una reescritura |
| 7 | **Estimación y cartera** | Estimar con rangos y calibrar; aprender de forma continua y diversificada | Prometes "dos semanas" exactas y quemas la confianza |

## Diagnóstico rápido — la parte accionable

Recórrelo antes de dar por buena una decisión de diseño. Cada "no" tiene acción.

| Pregunta | Si la respuesta es NO |
| --- | --- |
| ¿Puedo cambiar la base de datos sin tocar la lógica de negocio? | Falta repositorio/adaptador (ortogonalidad) |
| ¿Tengo ya una rebanada de punta a punta funcionando? | Construye la bala trazadora antes de ampliar |
| ¿Cada regla de negocio está definida en **exactamente** un sitio? | Identifica la fuente autoritativa y elimina las copias |
| ¿Un desarrollador nuevo llamaría "limpio" a esto? | Hay ventanas rotas: arregla ya, o entabla con ticket |
| ¿Mis estimaciones llevan rango y confianza? | Pasa a rangos (PERT), nunca a punto único |
| ¿Puedo revertir este despliegue en menos de 5 minutos? | Falta feature flag o despliegue reversible |
| ¿Estoy aprendiendo algo nuevo cada semana? | Cartera de conocimiento estancada |

## Los errores que más se repiten

- **DRY-ear código que solo *se parece*.** DRY va de conocimiento, no de
  sintaxis: dos bloques idénticos que sirven a reglas distintas **no** son
  duplicación, y unirlos los acopla.
- **Abstraer "por si acaso".** YAGNI también aplica a la flexibilidad: añade
  reversibilidad cuando tengas evidencia concreta de que la vas a necesitar.
- **Quitar aserciones en producción "por rendimiento".** Los bugs que cazaban
  pasan a corromper datos en silencio. Mide antes de quitar ninguna.
- **Estado global "por comodidad".** Destruye la ortogonalidad: todo acoplado a
  todo.
- **Aplazar la ventana rota.** El primer parche es el más caro, porque autoriza
  todos los demás.

## Puntuación

Al revisar o crear un diseño, puntúalo **0-10** contra estos principios, da la
cifra y di **qué falta concretamente** para llegar a 10. Una puntuación sin la
lista de brechas no sirve de nada.

## Referencias — abrir solo la que haga falta

- [references/element-tgde.md](references/element-tgde.md) — **la adaptación al
  dominio propio**: los 7 principios en ELEMENT/TGDE (bio-diseño predictivo), con
  el mecanismo que hace cumplir cada uno (watchdog anti-hardcode, preflight,
  separación `lib/` vs `input/`) y el score medido **8.7/10** (2026-07-18).
  **Léelo antes de tocar `element/lib/`.**
- [references/principios-detalle.md](references/principios-detalle.md) — los siete
  principios con su fundamento, ideas clave y tablas de aplicación (el texto que
  antes ocupaba este fichero).
- [references/dry-orthogonality.md](references/dry-orthogonality.md) — los cuatro
  tipos de duplicación; ortogonalidad en diseño y en test.
- [references/tracer-bullets.md](references/tracer-bullets.md) — bala trazadora vs.
  prototipo desechable; esqueletos que caminan.
- [references/contracts-assertions.md](references/contracts-assertions.md) —
  contratos, invariantes y programación asertiva.
- [references/broken-windows.md](references/broken-windows.md) — entropía, sopa de
  piedra, la rana hervida.
- [references/reversibility.md](references/reversibility.md) — desacoplar
  proveedores, evitar el bloqueo, decisiones bifurcadas.
- [references/estimation-portfolio.md](references/estimation-portfolio.md) — PERT,
  descomposición, cartera de conocimiento.

Fuente: Hunt & Thomas, *The Pragmatic Programmer*, 20th Anniversary Edition.
