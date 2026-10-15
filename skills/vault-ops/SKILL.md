---
name: vault-ops
description: "Mide, audita y mantiene el vault Obsidian que sirve de memoria a los agentes LLM (/mnt/f/OBSIDIAN). Úsala SIEMPRE que haya que dar cifras del vault (cuántas notas, cuántos tokens cuesta, enlaces rotos, qué falta indexar, cuánto de raw/ sigue sin digerir), antes de escribir cualquier auditoría del segundo cerebro, y después de una tanda de ediciones para comprobar que no se rompió nada. Prohíbe contar a mano: las cifras salen del script o no salen. Herramientas: auditoría de forma + censo de raw/bandeja sin leerlo, catálogo de Alejandría, linting epistémico de cifras canónicas, el eje Área/Tema del frontmatter (esquema_areas/generar_areas, con vocabulario cerrado que el CI hace cumplir), y sincronización con Notion (notion_sync censa el workspace y notion_fetch cierra los enlaces colgantes del volcado)."
version: 3.0.0
autor: "Kaitokid"
creado: 2026-07-28
---

# vault-ops — operar el segundo cerebro con cifras, no con impresiones

El vault de `/mnt/f/OBSIDIAN` es la memoria compartida entre herramientas LLM. Su
valor depende de dos cosas medibles —que el mapa quepa en el contexto y que los
enlaces no mientan— y de una que no se puede medir: que lo que dicen las notas
sea cierto. Esta skill cubre lo medible y **deja explícito lo que no cubre**.

## Regla dura

> **Ninguna cifra del vault se cuenta a mano.** Sale de `vault_audit.py` o no se
> publica.

Un conteo manual es correcto el día que se hace y falso la semana siguiente. Ya
pasó: una auditoría en prosa publicó "780 enlaces" cuando eran 779, y las cifras
de escala de la memoria del agente quedaron rancias (74 notas cuando ya había 86).
El script es la representación única y autoritativa de ese conocimiento.

## Las herramientas

| Script | Responde a |
| --- | --- |
| `certificar.sh` | **La compuerta.** Corre todo lo demás y sale con 1 si algo falla |
| `vault_audit.py` | ¿Cómo está la **forma**? Escala, frontmatter, índice, enlaces rotos, higiene, censo de `raw/` |
| `alejandria_index.py` | Regenera el **catálogo** de la biblioteca de documentos extensos |
| `claim_lint.py` | ¿El Vault **se contradice a sí mismo**? Hace cumplir las cifras canónicas |
| `consulta.py` | **El backend**: fragmentos a medida con presupuesto de tokens, para agentes |
| `triaje.py` | Clasifica `raw/bandeja/` con el modelo LOCAL y propone destino |
| `respaldo.ps1` | Espejo a disco físico distinto; se niega a correr si es el mismo |
| `esquema_areas.py` | Inyecta el eje **Área/Tema** en el frontmatter de `wiki/` |
| `generar_areas.py` | Escribe las páginas de Área (`wiki/AREAS/`) |
| `notion_fetch.py` | Cierra los huecos del volcado de Notion (marcadores colgantes) |
| `notion_sync.py` | Censa el workspace de Notion y baja lo que falte en disco |

### El eje Área/Tema (`esquema_areas.py`, `generar_areas.py`)

Desde 2026-07-30 `wiki/` se navega por dos ejes: el índice (tema del
conocimiento) y `area:`/`tema:` en frontmatter (área de la vida), resuelto por
**Dataview**. Vocabulario **cerrado** de 9 Áreas; `vault_audit.py --ci` **falla**
si una nota declara un área fuera de él, porque una nota mal etiquetada
desaparece de las consultas **sin ningún error visible** — el modo de fallo más
caro de un esquema por propiedades.

```bash
S=/mnt/f/skills/_personales/vault-ops/scripts
python3 $S/esquema_areas.py /mnt/f/OBSIDIAN            # simulacro
python3 $S/esquema_areas.py /mnt/f/OBSIDIAN --aplicar  # idempotente: salta lo ya etiquetado
python3 $S/generar_areas.py /mnt/f/OBSIDIAN            # --forzar para sobrescribir
```

⛔ **Un Área o un Tema NO genera archivo.** Son propiedades. El Notion anterior
tenía Áreas, 28 Temas y 25 fichas de Objetivos como páginas, y casi todas
estaban vacías. Una página de Área existe solo por lo que Dataview no puede
generar: la definición de qué entra y qué no.

### Sincronizar con Notion (`notion_fetch.py`, `notion_sync.py`)

Hacen preguntas distintas y hay que saber cuál toca:

| Script | Pregunta |
| --- | --- |
| `notion_fetch.py` | *"¿qué enlaces del volcado quedaron colgando?"* — busca `_(destino fuera del volcado: <uuid>)_` y baja esos destinos |
| `notion_sync.py` | *"¿qué existe en Notion que no esté en disco?"* — censo `/v1/search` + diff contra los `notion_id:` de `raw/` |

```bash
T=/mnt/f/src/api/api/notion.txt          # el token se pasa por RUTA, nunca por valor
python3 $S/notion_sync.py /mnt/f/OBSIDIAN --token-file $T --cache /tmp/censo.json
python3 $S/notion_sync.py /mnt/f/OBSIDIAN --token-file $T --cache /tmp/censo.json \
        --excluir "Daily Habits" --bajar          # reanudable: no repide lo ya bajado
```

> **Lección del 2026-07-30, la que justifica que existan los dos:** el volcado
> del 26-jul daba el Notion por migrado con 1 401 objetos. El censo encontró
> **4 219**, con **3 308 ausentes creadas antes** de aquella fecha — o sea, no
> era crecimiento. *Un inventario nunca debe salir de la misma fuente que el
> mapa: mientras coincidan por construcción, no pueden avisarte de nada.*

### La compuerta única

```bash
bash /mnt/f/skills/_personales/vault-ops/scripts/certificar.sh
```

Seis comprobaciones —estructura, catálogo, cifras canónicas, respaldo de menos
de 24 h en otro disco, historial—. **Es el análogo de `preflight.py` en ELEMENT**:
los documentos pasivos no cambian la conducta, un comando que falla sí.

### El backend para agentes (`consulta.py`)

Un modelo local no puede abrir el vault: cargarlo cuesta ~107 000 tokens. Llama
aquí y recibe fragmentos con procedencia, dentro de presupuesto, en **~0,5 s**:

```bash
python3 .../consulta.py "términos de la duda" --tokens 800 --json
python3 .../consulta.py --nota "Título exacto"     # una nota entera
python3 .../consulta.py --mapa                     # qué catálogos hay y qué cuestan
```

Determinista a propósito: sin embeddings, sin servicio, sin base vectorial. A
esta escala se recorre todo en medio segundo, y una capa vectorial sería una
**segunda representación del conocimiento que divergiría** del Markdown.

### Triaje con el modelo local (`triaje.py`)

```bash
python3 .../triaje.py --n 0        # clasifica todo lo pendiente (reanudable)
python3 .../triaje.py --informe    # qué decidió
python3 .../triaje.py --aplicar    # mueve SOLO el ruido, a raw/descarte/
```

⛔ **`think:false` es obligatorio.** Qwen3.5 es un razonador: sin desactivarlo
gastó 900 tokens y 22 s para devolver una respuesta **vacía**. Con
`think:false` + `format:json` + `temperature:0`: JSON válido en **0,35 s**.

⚠️ **La confianza que emite está saturada** (solo 0.98 y 1.00): no discrimina y
**no sirve como compuerta**. La defensa real son las postcondiciones
deterministas — p. ej. un documento de <4 KB no puede ir a Alejandría por mucho
que el modelo insista, porque "vale por su texto íntegro" es falso para un
abstract.

## Uso

```bash
S=/mnt/f/skills/_personales/vault-ops/scripts/vault_audit.py

# Reporte a stdout (lo normal antes de escribir una auditoría)
python3 "$S" /mnt/f/OBSIDIAN

# Persistir métricas + reporte
python3 "$S" /mnt/f/OBSIDIAN --json /tmp/vault.json --md /tmp/vault.md

# Censo de la bandeja: QUÉ hay, sin abrir un solo archivo
python3 "$S" /mnt/f/OBSIDIAN --censo-raw /tmp/censo.csv
```

## Qué mide

| Bloque | Responde a |
| --- | --- |
| **Escala y economía** | ¿Cuánto costaría cargar `wiki/` entero? ¿Cuánto ahorra entrar por `index.md`? ¿A cuántos tokens por nota sale el índice? |
| **Disciplina formal** | ¿Qué notas no tienen los 4 campos de frontmatter? ¿Cuáles no están indexadas? ¿Hay vacías o con nombre duplicado? |
| **Grafo** | ¿Cuántos enlaces hay? ¿Qué notas son islas? ¿Cuáles no tienen backlinks? **¿Qué enlaces están rotos?** ¿Alguna transclusión apunta a un archivo que no existe? |
| **Honestidad epistémica** | ¿Qué proporción de notas marca sus propios límites con `⚠️`? |
| **Higiene** | ¿Hay notas sueltas fuera de `wiki/`? ¿Hay sub-bóvedas `.obsidian` anidadas? |
| **Ingestión** | ¿Cuánto de `raw/` sigue sin digerir, por grupo y por extensión? |

### Catálogo de Alejandría

```bash
python3 /mnt/f/skills/_personales/vault-ops/scripts/alejandria_index.py /mnt/f/OBSIDIAN --escribir
```

Se regenera **en la misma operación** en que entra un documento. Un catálogo
mantenido a mano se desincroniza, y uno desincronizado es peor que ninguno.
Falla si hay IDs `AL-####` duplicados; reporta como huérfano todo documento sin
`al:` o sin `resumen:`.

### Linting epistémico (cifras canónicas)

```bash
python3 .../claim_lint.py /mnt/f/OBSIDIAN              # exit 1 si hay contradicción
python3 .../claim_lint.py /mnt/f/OBSIDIAN --descubrir  # para POBLAR el registro
```

DRY aplicado a los números: una cifra portante se declara **una vez** en
`wiki/SISTEMA/Cifras Canónicas.md` y el script comprueba que ninguna nota la
contradiga. Sirve de compuerta antes de cerrar una tanda de ediciones.

**Por qué registro y no barrido ciego**: agrupar todos los `R²` del Vault devuelve
un pajar (16 notas, 19 valores, casi todos legítimos porque son experimentos
distintos). El registro invierte el problema — solo se vigila lo que alguien
declaró portante, y ahí una discrepancia **sí** es señal. El modo `--descubrir`
conserva el barrido, pero etiquetado como lo que es: ruidoso y solo para poblar.

⚠️ **Garantiza consistencia, no verdad.** Si el valor del registro es incorrecto,
el linter propagará el error con total disciplina.

## Qué NO mide (decirlo siempre al publicar)

**No verifica que el contenido sea cierto.** Una nota puede tener frontmatter
perfecto, estar bien enlazada, citar fuente con fecha y contener un número mal
copiado. Verificar cifras contra la fuente primaria es trabajo humano; el
precedente que lo justifica: la verificación de la ecuación de Antoine encontró
que 81,8 mbar correspondían a **42 °C** y no a los 37 °C que afirmaba el
documento — y salió de *recalcular*, no de releer.

## Trampas ya pagadas

- **Wikilinks partidos por salto de línea.** Obsidian **no** resuelve un `[[Nota
  con nombre largo]]` cortado a mitad por un `\n`. Al reflowear un párrafo se
  rompen enlaces en silencio. El script los descarta a propósito, así que
  aparecen como rotos — que es exactamente lo que son.
- **`[[ ]]` citado como ejemplo** en prosa contaba como enlace roto. Se filtra.
- **Sub-bóvedas anidadas.** Una carpeta con su propio `.obsidian/` dentro de
  `wiki/` mete decenas de nodos de configuración en cualquier análisis de grafo
  (llegó a ser el 50% del grafo). El script las detecta pero **no las borra**:
  si esa carpeta está abierta como bóveda en Obsidian, moverla destruye el
  workspace del usuario. Se reporta y se pregunta.
- **`_PRIVADO/` no se abre nunca.** El script confirma que existe y lo salta sin
  listar su contenido — contiene credenciales sin cifrar.
- **Separador de etiquetas en el registro: `;`, no coma.** Las comas chocan con
  los decimales españoles (`0,90` se partía en `0` y `90`, y `90` casaba con
  cualquier línea que tuviera un 90). Costó 36 falsos positivos.
- **Un número en la misma línea no es un número sobre lo mismo.** «RT-qPCR (n=4)»
  no afirma que la correlación valga 4. El linter solo compara números
  *comparables*: decimales si la canónica es decimal, y dentro de un factor 5.
  Cuando aun así otra métrica comparte línea (un `F1 = 1.00` junto a `RT-qPCR`),
  se declara en la columna `excluir` — mejor una vía de escape declarativa que
  afinar la regex indefinidamente.
- **Un linter que solo sabe decir «todo bien» no es de fiar.** Comprobar siempre
  que caza una violación real antes de creerle: se le inyectó el 0.84 purgado en
  una nota de prueba y lo detectó, dejando pasar el 0.90 correcto.
- El conteo de tokens es `caracteres / 4`, una **aproximación** para comparar
  magnitudes. No sirve para presupuestar al token y el reporte lo etiqueta.

## Después de medir

Si el reporte saca enlaces rotos, hay dos salidas legítimas y hay que elegir una:
**crear la nota**, o **degradar el enlace a texto plano con la ruta real del
archivo**. La segunda es la correcta cuando el destino es documentación de motor
que ya vive en un repo (`element/CONTRATO.md`): duplicarla como nota la haría
divergir. Un enlace roto no se distingue de un enlace a una nota futura, así que
dejarlo es la peor de las tres opciones.

## Relacionado

- Protocolo autoritativo del vault: `/mnt/f/OBSIDIAN/CLAUDE.md` — leerlo antes de
  escribir nada dentro.
- `wiki-mecanistico-robusto` — el rigor exigido al **contenido** de una nota.
  Esta skill mide la forma; aquella exige que la sustancia esté verificada.
