# Adaptación al dominio — ELEMENT / TGDE (bio-diseño predictivo)

Aplicación de los 7 principios Pragmatic a **ELEMENT** (predicción genoma+ambiente→fenotipo) y sus proyectos
(hamcao/fucosa, shewanella, ecoli). Se integra con **loop-engineering** (maker/checker): la compuerta mecánica
(`tools/preflight.py` + `tools/hardcode_watchdog.py`) ES el mecanismo de *Design by Contract* a nivel de sistema.

## Traducción de cada principio al dominio

| # | Principio | En ELEMENT significa | Mecanismo |
|---|---|---|---|
| 1 | **DRY** | La biología (reguladores, TF, genes, rutas) tiene UNA fuente: secuencia+anotación/GEM/config. **NUNCA** literales en `lib/`. | watchdog anti-hardcode |
| 2 | **Orthogonality** | `lib/` es genoma-agnóstico; los datos organismo-específicos viven en `input/raw/`. Cambiar de organismo = cambiar inputs, no código. | separación lib/ vs input |
| 3 | **Tracer bullet** | El pipeline `element couple` (genoma→predicción) es la bala trazadora end-to-end; el caso fucosa es la rebanada vertical completa (Spearman 0.90). | couple + caso guía |
| 4 | **Design by Contract** | Precondiciones en las funciones públicas (fail-early con mensaje claro) + la **compuerta** (preflight/watchdog) como contrato de sistema que aborta un commit inválido. | asserts + preflight |
| 5 | **Broken Windows** | 0 marcadores de deuda reales; legacy CUARENTENADO (código borrado: env_tilt_operator; docs a `legacy/`). No dejar "frontera" ni número inflado sin corregir. | legacy/ + watchdog baseline |
| 6 | **Reversibility** | GEM, genoma, medio, s_ETB son INPUTS (config), no estructura. Se cambia de GEM/organismo/sustrato sin tocar `lib/`. | project.yaml + feedstock |
| 7 | **Estimation/Portfolio** | Métricas con RANGO y matiz honesto (Spearman 0.90 ranking; magnitud GEM-bounded; curva R²(n) = requerimiento medido). *hypothesis non fingo*. | held-out + curva R²(n) |

## Evaluación de madurez (score Pragmatic, 2026-07-18)

| Principio | Score | Base | Para 10/10 |
|---|---|---|---|
| 1 DRY | **8** | watchdog verde; única duplicación: 4 copias idénticas de skill `tgde-memoria` (sincronizadas) | generar las 4 desde una fuente |
| 2 Orthogonality | **9** | lib/ genoma-agnóstico; operadores legacy borrados | — |
| 3 Tracer bullet | **9** | couple end-to-end + fucosa vertical | — |
| 4 Design by Contract | **8** ↑ (era 6) | **añadidas precondiciones a `sensor_screen` (build_gene2rxns/regulon_genes/regulon_magnitude/differential_trace)**; compuerta como contrato de sistema | extender contratos a `feedstock`, `derived_tilt`, `pathway_landscape_coupling` |
| 5 Broken Windows | **9** | 0 deuda real (los "TODO" eran la palabra española); legacy cuarentenado | monitorear entropía en CI |
| 6 Reversibility | **9** | GEM/genoma/medio como config | — |
| 7 Estimation | **9** | rangos honestos, curva R²(n), non fingo | — |
| **GLOBAL** | **~8.7 / 10** | Programa maduro; disciplina fuerte | contratos en el resto de `levelc/` + consolidar skill duplicada |

## Cómo usar esto (loop maker/checker)
Antes de commitear cualquier cambio en `element/lib/`: **maker** hace el cambio; **checker** corre
`preflight.py` + `hardcode_watchdog.py --check` (deben salir VERDE) + smoke test de los contratos nuevos. Si algo sale
ROJO → REJECT, arreglar, repetir. Es el ciclo que maduró este mismo review (contratos añadidos → compuerta verde → 4/4 fail-early verificado).
