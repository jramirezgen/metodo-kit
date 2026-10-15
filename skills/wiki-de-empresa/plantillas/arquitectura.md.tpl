# Arquitectura corporativa de {empresa} (nodo BP0)

Estado: {fecha}. Decisión de diseño; la revisa quien firme BP99.

## 1. Dónde vive cada cosa (un almacén, una función)

| Almacén | Ruta | Qué guarda | Qué NO guarda | Versionado |
|---|---|---|---|---|
| **Base canónica** | `<ruta de datos y documentos controlados>` | originales (contratos, facturas), gobierno de datos, registro seudónimo, casos | borradores | fuera de git, con manifiesto SHA-256 |
| **Repo de gestión** | `<este repo>` | lo que se redacta y calcula: `docs/empresa/`, modelos, scripts, plan y registro del DAG | PII, PDFs firmados, datos sensibles | git |
| **Wiki de la bóveda** | `<carpeta del wiki>` | mapas, incidencias, navegación | fuente de verdad de nada | derivado y reemplazable |
| **Repos técnicos** | `<repos de producto>` | el software | documentos de empresa | git, reemplazables |

Regla de oro: un dato vive en un almacén y se referencia desde los demás por ruta o por hash; nunca se copia. Una sola copia de trabajo por repo.

## 2. Capas
Dirección y plan (`docs/empresa/NN_*`) · Procesos (SOP) · Sistemas (CRM, ERP mínimo, data warehouse) · Datos (registro seudónimo, identidad aparte) · Análisis (`analisis/matlab`, `analisis/r`).

## 3. Cadena de análisis
- Una sola fuente de cifras: el módulo de supuestos exporta `supuestos.json`; MATLAB y R lo leen. Ninguna cifra se teclea en un script.
- Cada análisis: script versionado + salida en `analisis/salidas/` + comando que la reproduce.

## 4. Reglas
1. Cifra con fuente y fecha; supuesto marcado; no verificado `⚠️`.
2. Sin PII ni nombres de terceros en git.
3. Los estudios previos y la investigación asistida son **insumo a verificar**, no verdad.
4. Se escribe para el MVP del primer cliente y se declara lo que se difiere.
