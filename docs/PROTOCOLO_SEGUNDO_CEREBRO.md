# Protocolo del vault (CLAUDE.md del segundo cerebro)

> Plantilla genérica. Si tu agente no es Claude Code, guárdala como `AGENTS.md`. Edita las rutas.

## 1. Acceso por capas
- `wiki/` (síntesis): leer y editar por iniciativa propia cuando sea relevante para la tarea. No barrerla.
- `alejandria/` (documentos extensos): consultar `INDICE.md` libremente; abrir **un** documento a la vez, a petición o cuando el contexto lo pida.
- `raw/` (sin curar): **orden explícita** para leer, procesar o digerir.
- `_PRIVADO/`: no se toca.

## 2. Ignorar siempre
`.gdoc/.gsheet/.gslides`, `node_modules/`, `.git/`, `.venv/`, `dist/`, repos de terceros (`*-main/`, `vendor/`), `archive/`, `snapshot_*`. Si una petición amplia los alcanzaría, avisar.

## 3. Secretos
No viven en el vault. Punto único de credenciales fuera de él. Se pasan por ruta (`--token-file`), nunca por valor; no se imprimen ni truncados.

## 4. Orientarse vs buscar
`index.md` una vez para orientarse; después `consulta.py "tema" --tokens 400 --k 3`. Nunca barrer `wiki/` completa.

## 5. Autoridad epistémica local
Si una nota contradice lo que el modelo cree saber, manda la nota. Prohibido sustituir en silencio el método local por el estándar o «corregir» una cifra local rara. Discrepar: declarado antes de actuar (nota, motivo, qué cambia). Contrapeso: lo marcado `⚠️ sin verificar` es hipótesis explícita; no se extrapola ni decide nada caro.

## 6. Reglas duras de escritura
Síntesis nunca copia · una nota un concepto · cifra con fuente y fecha · `⚠️ sin verificar` en lo dudoso · no borrar, marcar obsoleta y enlazar la sustituta · indexar en la misma operación · fechas absolutas `AAAA-MM-DD`.

## 7. Flujo de ingestión (sólo bajo orden)
Leer el archivo de `raw/` → extraer entidades, conceptos, decisiones, cifras → escribir/actualizar notas en `wiki/` → enlazar en ambos sentidos → indexar → decidir destino del original (¿íntegro a Alejandría? ¿procedimiento repetible a skill? ¿descartar?).

## 8. Alejandría
`alejandria/[COLECCION]/AL-####_slug.md` con frontmatter `al`, `titulo`, `coleccion`, `fecha`, `estado`, `origen`, `resumen` (dice **cuándo hace falta**, no de qué trata). El `AL-####` es global y nunca se reutiliza. El catálogo se genera (`alejandria_index.py --escribir`), no se edita. Anidar colecciones según la jerarquía real del proyecto, no con sufijos de nombre.

## 9. Área/Tema
`area:` vocabulario cerrado (decídelo para tu caso; el original usó nueve); `tema:` abierto. Un Área o Tema **no genera archivo**: son propiedades, y el listado lo resuelve Dataview.

## 10. Infraestructura
Código fuera del vault; un solo árbol de trabajo por repo; espejos bare no editables; respaldo en disco físico distinto. Sin respaldo no hay seguridad: declarar la fecha del último.
