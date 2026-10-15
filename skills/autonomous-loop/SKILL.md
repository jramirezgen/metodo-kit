---
name: autonomous-loop
description: Disciplina de fase para trabajo largo y multi-sesión (brainstorm → plan → work → review → fix → compound → test → ship) con estado persistido y protocolo de re-anclaje contra pérdida de contexto. Cargar al emprender una feature completa que abarcará varias sesiones o reinicios de contexto, no un cambio de una sola sentada.
metadata:
  origen: "F:\\skills\\Programacion y matematicas\\autonomous-loop-1.0.0"
  extraido: 2026-09-06
---

# Autonomous loop: disciplina de fase para trabajo largo

## Cuándo aplica

Una feature completa que va a tomar varias sesiones o sobrevivir a reinicios
de contexto: investigar → planear → implementar → revisar → arreglar →
documentar → entregar. La señal es la duración, no la dificultad — un cambio
difícil pero de una sola sentada no lo necesita.

**No aplica** a un fix puntual, una pregunta, o cualquier cambio que termine
en la misma sesión donde empezó — ahí el overhead de mantener un archivo de
estado no se paga solo.

**Diferencia con este paquete tal como se distribuye**: el original trae un
Stop hook que bloquea la salida de la sesión y re-inyecta el prompt de fase
automáticamente, más comandos `/auto-loop` que invocan `/workflows:*` y
`/compound-engineering:*`. Esos plugins no están instalados en este
workspace, así que aquí se aplica la **disciplina** (fases + estado
persistido + re-anclaje), a mano, sustituyendo cada comando de fase por la
skill o el paso equivalente que sí existe aquí (tabla más abajo). No se
instaló el hook: exit de sesión sigue siendo normal, nadie bloquea nada.

## La máquina de fases

```
brainstorm → plan → work → review ──→ compound → test → ship
                              │                       │
                              ↓ (hallazgo grave)      ↓ (falla)
                             fix → re_review ───────→ fix
                              ↑       │
                              └───────┘ (máx. 3 ciclos)
```

| Fase | Qué produce | Equivalente en este workspace |
|---|---|---|
| brainstorm | Explorar QUÉ construir, dudas resueltas | Diálogo con el usuario antes de comprometerse a un plan |
| plan | Plan de implementación con research | Documento de plan (puede vivir en `docs/plans/` del repo en cuestión) |
| work | Implementación, commits incrementales | Aquí entra `code-principles`: TDD primero, luego las skills que la tarea pida |
| review | Hallazgos P1/P2/P3 | Skill `code-review` (o `/simplify` para solo limpieza) |
| fix | Hallazgos graves resueltos | Aplicar los arreglos; `defense-in-depth` si el hallazgo es de dato inválido |
| re_review | Verificar que el arreglo cerró el hallazgo | Repetir `code-review` sobre el diff |
| compound | Documentar el aprendizaje | Nota en memoria (`~/.claude/.../memory/`) o en `wiki/` del vault si aplica |
| test | Verificación end-to-end | Suite de tests del proyecto / skill `run` |
| ship | Entregar | Commit, push, PR |

`work`/`fix` son las fases donde **code-principles decide qué combinación de
las 8 skills de principios cargar** — este skill no las reemplaza, decide
cuándo entrar y salir de esa fase dentro del arco largo de la feature.

## Re-anclaje: protocolo contra la deriva de contexto

Al empezar cada sesión (o cada bloque largo de trabajo) sobre una feature en
curso, antes de escribir código:

1. Leer el archivo de estado (ver abajo) para saber la fase actual.
2. `git log --oneline -10` — qué se hizo de verdad, no lo que se recuerda.
3. `git diff --stat` — hay cambios sin commitear.
4. Releer el archivo de plan si existe.

Esto es lo que evita que un reinicio de contexto haga repetir trabajo o
perder de vista en qué fase estaba la feature.

## Estado persistido

Un archivo JSON (no markdown — un modelo lo corrompe menos) por feature en
curso, con al menos:

- `feature`, `phase`, `phases_completed`
- `phase_iteration` / `global_iteration` con límites (`max_phase_iterations`,
  `max_iterations`) para forzar avance si una fase se atasca
- `artifacts` (rutas a plan, PR, branch)
- `receipts`: prueba de que cada fase completada produjo algo verificable
  (`{"phase", "artifact", "git_sha", "timestamp"}`)
- `errors`: cuando algo falla, se registra aquí y **no se cambia de fase** —
  se reintenta la misma fase en la siguiente iteración

Reglas duras de actualización:

- Se actualiza **en cada frontera de fase**, nunca se difiere "para después".
- Terminar la feature entera se marca con una señal explícita e inequívoca
  (el original usa `<promise>SHIPPED</promise>`) — no dar por terminado algo
  que solo se "siente" terminado.
- Máximo de ciclos `fix → re_review` (default 3): si el hallazgo grave
  persiste después de eso, se escala al usuario en vez de seguir iterando a
  ciegas.

## Verificación antes de dar por cerrada una fase

- [ ] El estado quedó escrito con la fase, el receipt y el timestamp de esta
      transición — no solo en la cabeza de la conversación.
- [ ] Un error no avanzó la fase en silencio; quedó en `errors`.
- [ ] `work`/`fix` pasaron por las skills de `code-principles` que la
      situación pedía, no se saltaron por prisa de llegar a `ship`.
- [ ] `ship` solo se declara con la señal de completitud explícita, y con
      `review`/`test` en verde — nunca antes.
