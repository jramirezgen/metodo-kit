# {{FASE}} · ⟨qué cambia, en una línea⟩

Preinscrita el {{FECHA}}, **antes** de tocar el código.
Incidencias: ⟨INC-### que esta fase cierra o avanza⟩.
Orden: ⟨quién la pidió y con qué palabras, citadas⟩.

## 0. Qué es

Tipo: ⟨sin cambio de comportamiento / con cambio de comportamiento⟩. Una de dos:
- **Sin cambio de comportamiento** (refactor, traslado, procedencia): no debe mover ni un bit.
  Si el sello no sale idéntico, es un **bug del cambio**, no un hallazgo.
- **Con cambio de comportamiento** (física, reglas, datos): el delta esperado sale de
  `docs/CRITERIO_DELTA_ESPERADO.md`. Si coincide, se re-sella; si no, es hallazgo.

## 1. El cambio

⟨Lista numerada de lo que se toca, con fichero y, si aplica, el sha de cada insumo nuevo.⟩

## 2. Criterios (conjuntivos: fallar uno es fallar la fase)

| # | compuerta | pasa si |
|---|---|---|
| ⟨F.1⟩ | ⟨la comprobación rápida⟩ | ⟨resultado exacto: IDÉNTICO / banda numérica / rc 0⟩ |
| ⟨F.2⟩ | ⟨el sello completo en un brazo nuevo⟩ | ⟨…⟩ |
| ⟨F.3⟩ | ⟨la compuerta nueva muerde: un caso malo la hace fallar⟩ | ⟨…⟩ |
| ⟨F.4⟩ | ⟨suite en cada entorno que importa⟩ | ⟨verde; los saltos dicen qué falta⟩ |

## 3. Declarado antes

⟨lo que ya sabes que va a parecer raro, dicho ahora y no después⟩

## 4. Lo que esta fase NO hace

⟨Lo que queda para fases siguientes, con nombre. Evita el «ya que estoy».⟩
