# Criterio de delta esperado — cuándo un cambio re-sella y cuándo es hallazgo

⟨AAAA-MM-DD⟩. Rige las fases que cambian comportamiento a propósito.

> **Si el delta coincide con el esperado, se re-sella. Si no coincide, es hallazgo.**

| id | arreglo | alcance medido | delta esperado |
|---|---|---|---|
| ⟨M2⟩ | ⟨…⟩ | ⟨…⟩ | ⟨qué se mueve, en qué sentido y orden de magnitud; qué NO se mueve⟩ |

**Primer candidato:** ⟨el de evidencia cuantitativa más fuerte, no el más urgente, con la cifra⟩.

## Cómo se aplica

1. Un arreglo por brazo: dos a la vez confunden sus deltas.
2. Cada arreglo preinscribe su fila traducida a observables con banda, **incluidos los que no deben moverse**.
3. Antes del arreglo, el sello vigente pasa (hooks y CI verdes).
4. Coincide → sello nuevo en su propia carpeta; el anterior se congela, no se borra.
   No coincide → incidencia antes de tocar nada más.
5. Un cambio que no está en la tabla y mueve el sello es un bug.
