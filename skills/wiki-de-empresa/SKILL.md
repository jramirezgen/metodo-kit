---
name: wiki-de-empresa
description: "Crea y mantiene la wiki corporativa de una empresa como un repo con DAG: plan de negocio completo (modelo, propuesta de valor, mercado, competencia, clientes, viabilidad, marca, comercialización, relación con clientes, operaciones, riesgos, permisos mínimos del MVP, personas, finanzas, proyecciones, crecimiento), sistemas (CRM, ERP mínimo, data warehouse con capas), análisis con MATLAB y R, revisiones adversariales por bloque y un dossier para el primer cliente. Úsala al montar o auditar la parte corporativa de una empresa nueva. Hermana de wiki-de-proyecto (un repo) y wiki-de-personas (una persona); la unidad aquí es la empresa."
license: MIT
metadata:
  version: "0.1.0"
  autor: "Kaitokid"
  creado: "2026-10-12"
  actualizado: "2026-10-12"
---

# wiki-de-empresa — la empresa como repo con plan verificable

Nace de SAPYRIA (2026-10-12), primer cliente de la skill. Hermana de [[wiki-de-proyecto]] y [[wiki-de-personas]], pero con cuatro diferencias que cambian las reglas:

1. **Hay tres almacenes y uno solo es git.** Base canónica de datos y documentos controlados (fuera de git, con SHA-256) · repo de gestión (lo que se redacta y calcula) · wiki de la bóveda (derivado, reemplazable) · repos técnicos. *Un dato vive en un almacén y se referencia desde los demás; nunca se copia.*
2. **Mucha de la información de partida es investigación asistida sin verificar.** Se trata como **insumo a cotejar**, nunca como verdad. Lo que no se coteja queda `⚠️ sin verificar`.
3. **Las cifras tienen una sola fuente** (`supuestos.py` → `supuestos.json`) que leen MATLAB y R. Ninguna cifra se teclea en un script.
4. **El producto es un dossier para un cliente real**, así que lo interno (⚠️, borradores, notas) nunca viaja en él.

## Los comandos

```bash
S=/mnt/f/skills/_personales/wiki-de-empresa/scripts
python3 $S/instalar.py <repo> --empresa NOMBRE --enlaces enlaces.json            # ensayo
python3 $S/instalar.py <repo> --empresa NOMBRE --enlaces enlaces.json --aplicar  # instala / pone al día
python3 $S/auditar.py <repo>                                                      # compuerta (0 = pasa)
```

Requisito: el repo ya tiene el DAG estándar ([[dag-de-proyecto]]). `instalar.py` **nunca pisa** lo que existe en `docs/empresa/`; solo actualiza lo vendorizado (`plan/nodos_empresa.py`, que lleva el catálogo embebido para que el repo siga autónomo con `/mnt/f` desmontado).

## Qué instala

| Pieza | Dónde | De quién |
|---|---|---|
| Catálogo de 28 nodos (`BP*`, `BPR*`, `SI*`) | `plan/nodos_empresa.py` | vendorizado |
| Enlaces a los nodos propios de la empresa y textos extra | `plan/enlaces_empresa.json` | de la empresa |
| Arquitectura corporativa + un esqueleto por capítulo con sus secciones | `docs/empresa/` | de la empresa |
| Sistemas: arquitectura con mapa de capas, esquema SQL sin identidad, almacén operable | `docs/empresa/sistemas/`, `analisis/dwh/` | de la empresa |
| Análisis: exportar supuestos, plantilla MATLAB, plantilla R | `analisis/` | de la empresa |
| Prueba de no-divergencia y de auditoría | `tests/test_wiki_empresa.py` | vendorizado |
| Generador de paquetes de revisión externa por rol (abogado, contador) y su configuración `paquetes.json` | `docs/validacion/generar_paquetes.py` | de la empresa (plantilla) |

## El plan (frente `BP`/`SI`), en el orden en que depende

`BP0` arquitectura → `BP1` inventario → `BP2` modelo de negocio y propuesta de valor → `BP3` mercado → `BP4` competencia y posicionamiento → `BP5` clientes → `BP6` viabilidad y escalabilidad (MATLAB) → `BP7` marca → `BP8` comercialización y precios → `BP9` relación con clientes → `BP10` plan operativo → `BP11` riesgos → `BP12` permisos mínimos → `BP13` personas y administración → `BP14` finanzas → `BP15` proyecciones → `BP16` crecimiento y medición. Sistemas: `SI0` arquitectura por capas → `SI1` esquema → `SI2` almacén con ETL → `SI3` las siete transversales. Cada bloque cierra con su **revisión adversarial** (`BPR1`–`BPR5`); `BP98` es el dossier del cliente y `BP99` la revisión final.

## Las reglas duras

1. **Una sola fuente de cifras.** Un `.m` o `.R` con una cifra de 4 o más dígitos tecleada **falla** la auditoría.
2. **Un capítulo sin `POR COMPLETAR` ni secciones vacías, o no se cierra.** Cerrar exige un commit que toque la entrega (regla de dag-de-proyecto) y que `auditar.py` pase.
3. **Cada bloque lleva su revisión adversarial independiente** (solo lectura, sin leer el chat, con las decisiones cerradas del usuario como no negociables). Cada hallazgo se **verifica contra el texto** antes de aceptarlo y **entra al tablero de incidencias antes que al capítulo**.
4. **Sin PII ni nombres de terceros en git.** Lo comprueba la auditoría (DNI de 8 dígitos, correos, móviles).
5. **El sistema se diseña por capas** (presentación, API, aplicación, dominio, datos, integración) y con las siete transversales (configuración, errores, observabilidad, reproducibilidad, seguridad, concurrencia, empaquetado); el dominio no importa lo transversal. Ver [[code-principles]] «un 10/10 se audita con dos lentes y un tercero».
6. **Se escribe para el MVP del primer cliente** y se declara lo que se difiere. Lo regulatorio se limita al mínimo necesario y se lista lo que exigiría crecer.
7. **Lo que no se mueve sin orden:** los originales de la base canónica y cualquier dato clínico o personal. Se propone, se pide autorización, se verifica por hash antes de borrar.

8. **La validación externa se entrega como paquete generado por rol** (plantilla `validacion/generar_paquetes.py`): preguntas filtradas por
   clase, sin rutas internas, con tabla de respuestas y anexos autorizados; una prueba exige que lo commiteado coincida con lo generado.
9. **Cerrar es honesto:** un ensayo con datos ficticios se llama ensayo; un experimento con n por debajo de su umbral es inconcluso; los
   mapas se prueban contra su generador y se republican en cada cierre (lecciones 20–28).

## Lo que NO hace (declarado)
- No escribe el contenido de los capítulos: los esqueletos fuerzan estructura, no verdad.
- No sustituye al abogado ni al contador: marca como nodo lo que depende de ellos.
- No decide qué CRM/ERP comprar: fija el umbral para decidirlo (SI0).

Lecciones del primer cliente: `referencias/LECCIONES.md`.
