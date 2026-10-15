# -*- coding: utf-8 -*-
"""El mapa del propio sistema: qué es un **wiki repo** y por dónde va la vuelta.

Este generador es el único caso en que el sistema se dibuja a sí mismo. Sirve
para lo que el usuario pidió: *«me gustaría tener una repo wiki para la misma
repo wiki y con su canvas para analizarlo en el futuro»* — es decir, poder mirar
la arquitectura entera dentro de Obsidian, con sus compuertas y sus huecos, en
vez de reconstruirla leyendo siete ficheros.

**Todas las cifras están medidas el 2026-09-08** contra el disco: las siete
piezas y sus líneas, lo publicado en `wiki/ELEMENT/`, las tres divergencias de
`publicar.py` y la geometría de la compuerta de legibilidad. Ninguna se teclea
de memoria; lo que aún no existe se dibuja **nombrado**, no rellenado.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from canvas_lib import Lienzo, informe   # noqa: E402  (vendorizado)

L = Lienzo()
C = L.columnas("leyenda", "repo", "compuertas", "boveda", "humano", desde=-1400)

Y0 = -1200

# ── leyenda y tesis: fuera de todo grupo, y por eso «libres» ────────────────
L.nodo("leyenda", C["leyenda"], Y0, L.ancho, 340, """## El wiki repo — el sistema visto por dentro
*skill `wiki-de-proyecto` v2.0.0 · cifras medidas el 2026-09-08*

🟪 arquitectura · 🟦 lo que el repo guarda · 🟨 compuerta
🟩 lo que la bóveda tiene hoy · 🟧 lo que hace una persona
🟥 hueco o deuda declarada

**Se lee de izquierda a derecha, y se vuelve por abajo.**""", "6")

L.nodo("tesis", C["leyenda"], Y0 + 460, L.ancho, 420, """## La tesis en una frase

La documentación viva de un proyecto **no cabe en el repo**: se lee y se anota
en Obsidian, donde no hay historia. Y **no cabe sólo en la bóveda**: ahí no hay
`diff`, ni `status`, ni nadie que impida pisar lo de ayer.

Un **wiki repo** parte la diferencia como git: el repo guarda la **intención**
(los generadores y `wiki.json`), la bóveda es el **árbol de trabajo**, y entre
los dos hay seis compuertas y un `.lock` con dos huellas.

⚠️ No es un exportador. Un exportador pisa; esto **se niega a pisar**.""", "6")

# ── columna 1 · lo que el repo guarda ──────────────────────────────────────
r = L.pila("repo", Y0)
r.add("r_manifiesto", 380, """## 1 · `wiki.json` — la INTENCIÓN
*el equivalente del índice de git*

Declara `proyecto`, `vault`, `estructura` (dónde va cada cosa dentro de
`wiki/<PROYECTO>/`), el `frontmatter` que heredan las notas generadas, y las
listas `mapas[]` y `bases[]` con su numeración densa.

**ELEMENT hoy: 2 mapas · 3 bases.**

Aquí —y sólo aquí— vive lo que sabe de qué proyecto se trata.""", "5")
r.add("r_generadores", 320, """## 2 · `generar_*.py` — la FUENTE
*el `.canvas` y el `.base` son artefactos, no fuentes*

Un mapa mantenido a mano se desincroniza, y un mapa desincronizado es peor que
ninguno **porque se sigue creyendo**.

ELEMENT: 3 generadores propios (`canvas`, `lazo`, `ecuaciones`) + 2
vendorizados que valen para cualquier proyecto (`incidencias`, `versiones`).""", "5")
r.add("r_piezas", 360, """## 3 · las 7 piezas VENDORIZADAS
`canvas_lib` · `base_lib` · `wiki_repo_lib` · `publicar`
`archivar` · `generar_incidencias` · `generar_versiones`

**2 532 líneas de stdlib pura**, copiadas y no enlazadas: el repo tiene que
seguir siendo autónomo aunque `/mnt/f` no esté montado.

> Se vendoriza **lo que no tiene política**. Lo del proyecto vive en
> `wiki.json`, nunca dentro del código copiado.""", "5")
r.add("r_lock", 300, """## 4 · `wiki.lock.json` — lo OBSERVADO
*generado; no se edita a mano*

Por artefacto, **dos** huellas: la canónica del repo **y** la de la bóveda tal
como quedaron la última vez.

Hacen falta las dos —igual que el índice de git recuerda el blob *y* el árbol—
o adoptar una edición manual la dejaría pisable en la corrida siguiente.""", "5")
r.cerrar("g_repo", "EL REPO — la intención, versionada en git", color="5")

# ── columna 2 · las compuertas ─────────────────────────────────────────────
c = L.pila("compuertas", Y0)
c.add("c_legible", 380, """## A · legibilidad del canvas
`canvas_lib.validar()`

La etiqueta de una arista es una **caja**, no un punto: mide 188–248 px y se
pinta en el punto medio de la curva.

Con paso 800, nodo 620 y padding 60 → **60 px de corredor**, y **6 de 13
etiquetas quedaron detrás de un nodo**. La primera compuerta miraba el *punto*
medio y dio verde con las seis tapadas delante.

Hoy: paso **1400** ⇒ corredor **660**. No escribe si falla.""", "3")
c.add("c_base", 340, """## B · la Base alcanza notas de verdad
`base_lib.validar()`

La ruta de un filtro es relativa a la **raíz de la bóveda**, y este disco tiene
dos que contienen `wiki/ELEMENT/`. Las dos primeras Bases salieron **vacías** y
Obsidian no dice por qué.

`raices_de_boveda()` mide en disco qué directorios tienen `.obsidian/` y emite
un `inFolder` por cada uno. Una columna que **ninguna** nota declare es
problema **duro**.""", "3")
c.add("c_indexado", 260, """## C · lo publicado está enlazado
`publicar._comprobar_indexado()`

La nota puerta `<PROYECTO>.md` tiene que enlazar cada índice, o no se publica
nada. Es la regla del vault —*se indexa en la misma operación*— hecha
compuerta.

Da el renglón exacto que falta; no lo escribe él.""", "3")
c.add("c_no_pisar", 300, """## D · no se pisa lo que alguien tocó
`wiki_repo_lib.situacion()`

Si la huella de la bóveda no es la del `.lock`, hubo edición manual: publicar
**se niega**. O se adopta (`--adoptar`, que es `git add`), o se queda.

`procedencia: manual` en `wiki.json` va más lejos: ese artefacto **nunca** se
sobrescribe; el sistema sólo lo numera, lo ficha y lo indexa.""", "3")
c.add("c_archivo", 320, """## E · ningún diseño anterior se pierde
`archivar.py` + `generar_versiones.py`

Antes de pisar un mapa se copia el vigente a `Versiones/` **con su nota**, que
transcluye el lienzo y dice qué nodos nacieron, murieron o cambiaron.

Cuatro reglas lo mantienen archivo: canvas ↔ nota siempre en pareja · `mapa_n`
nombra un mapa declarado · `version` única por mapa · **la `huella` es la del
canvas archivado**.""", "3")
c.add("c_indexa_archivo", 340, """## F · publicar corre los generadores declarados
`publicar.py` → el `generador` de cada Base

Una Base es una **consulta** y no deja enlace: la única arista del grafo hacia
esas notas es la lista de `[[enlaces]]` de su índice, y ese índice lo escribe su
generador. Publicar sólo lo **nombraba** —copiaba el `.base` y preguntaba «¿lo
corriste?»—, así que el índice se quedaba con lo de la última vez a mano.

Mordió dos veces seguidas: la v2 de un lazo se archivó bien y **nació sin
índice**; al día siguiente una incidencia escrita a mano se publicó y salió como
**no indexada** en la auditoría. Hoy corren todos, antes de las Bases porque un
índice las transcluye. Un generador declarado que no existe **es un fallo**.""",
      "3")
c.cerrar("g_compuertas", "LAS SEIS COMPUERTAS — lo que impide que esto se pudra",
         color="3")

# ── columna 3 · la bóveda ──────────────────────────────────────────────────
b = L.pila("boveda", Y0)
b.add("b_puerta", 280, """## `<PROYECTO>.md` — la nota puerta
*la escribe una persona; el sistema sólo la comprueba*

Es el eslabón `index.md → puerta → carpeta`. Sin ella lo publicado existe en el
disco y **no existe para nadie**.

`wiki/SISTEMA/` vivía con 52 notas y sin puerta hasta hoy.""", "4")
b.add("b_mapas", 260, """## `Mapas/` — los `.canvas`
`01 — …`, `02 — …`, numeración densa siempre.

Más su índice generado `00 — Mapas de <titular>`, que da el orden de lectura.

**wiki/ELEMENT/: 3 canvas publicados.**""", "4")
b.add("b_bases", 280, """## `Bases/` — bases NATIVAS de Obsidian
`.base`, no Dataview: se filtran y se ordenan en la interfaz.

**wiki/ELEMENT/: 3 bases** — ecuaciones, incidencias y versiones, cada una con
su nota `00 — …` que la abre y la explica.""", "4")
b.add("b_incidencias", 300, """## `Incidencias/` — el tablero
Una nota por incidencia: `inc` · `situacion` · `tipo` · `peso` · `mapa_n` ·
`nodo` · `bloqueado_por`.

`tipo` (`defecto · rfc · mejora`) existe porque **un RFC no es un defecto**: no
denuncia una falta, propone arquitectura.

**wiki/ELEMENT/: 14 incidencias.**""", "4")
b.add("b_versiones", 260, """## `Versiones/` — el histórico de diseños
`NN — <título> (vN, AAAA-MM-DD).canvas` y su nota.

Nunca borra: sólo añade. Es lo que hace que republicar no sea perder.

**wiki/ELEMENT/: 1 diseño archivado.**""", "4")
b.cerrar("g_boveda", "LA BÓVEDA — el árbol de trabajo: 73 notas de ELEMENT",
         color="4")

# ── columna 4 · lo que hace una persona (el retorno del lazo) ──────────────
h = L.pila("humano", Y0)
h.add("h_lee", 240, """## 1 · lee y anota en Obsidian
Es para lo que existe todo esto. Los mapas se abren, se navegan y se comentan
donde el resto del segundo cerebro ya vive.""", "2")
h.add("h_edita", 280, """## 2 · edita a mano
*y esto es una función, no un accidente*

Mover un nodo, corregir una frase, escribir una incidencia. `situacion()` lo ve
igual que `git status` ve un fichero sucio.""", "2")
h.add("h_adopta", 300, """## 3 · adopta, o no
`publicar.py --adoptar`  ≡  `git add`

Adoptar guarda la huella de la bóveda en el `.lock`: a partir de ahí, esa
edición es la verdad y el generador tendrá que respetarla.

**No adoptar también es una decisión**: publicar seguirá negándose.""", "2")
h.add("h_declara", 300, """## 4 · cambia la INTENCIÓN
Editar `wiki.json` o el generador es lo que de verdad cambia el diseño. Todo lo
demás son artefactos.

Y luego indexa en la bóveda **en la misma operación**:
`index.md` (o el sub-mapa) + `vault_audit.py`.""", "2")
h.cerrar("g_humano", "LA PERSONA — dónde el sistema le cede el mando", color="2")

# ── la vuelta del lazo: una fila propia, porque una arista larga no explica ──
# El primer intento envolvía las cuatro columnas en una banda `g_lazo`. La
# compuerta lo rechazó —«grupos solapados a medias»— y tenía razón: un grupo que
# contiene a otros tres no dice nada que las columnas no dijeran ya, y en
# Obsidian arrastrarlo arrastra el canvas entero. El retorno se dibuja como lo
# que es: **dos** cosas distintas que vuelven a **dos** sitios distintos.
YR = Y0 + 2690
L.nodo("v_adopta", C["boveda"], YR, L.ancho, 260, """## vuelve al `.lock`: **la huella**
Adoptar no cambia el diseño: cambia lo que el sistema **cree que hay** en la
bóveda. A partir de ahí, esa edición manual es la verdad y el generador tendrá
que respetarla o negarse.""", "2")
L.nodo("v_declara", C["compuertas"], YR, L.ancho, 260, """## vuelve a `wiki.json`: **el diseño**
Lo único que cambia de verdad el mapa es la intención. Retocar el artefacto es
retocar la salida de una función y esperar que la función cambie.""", "2")
L.envolver("g_lazo", "LA VUELTA — qué regresa de la bóveda al repo, y adónde",
           ["v_adopta", "v_declara"], color="6")

# ── banda inferior · lo que hoy no cierra ──────────────────────────────────
YD = Y0 + 3290
L.nodo("d_consumidor", C["repo"], YD, L.ancho, 360, """## 🟥 quien estrene el tercer wiki repo se queda fuera
`test_vendorizado.py` declara **2 consumidores** —`element/docs/wiki` y el
`docs/wiki/` de la propia skill— y desde hoy la suite de ELEMENT **ejecuta los
cuatro comprobadores de la skill**, no sólo compara su propia copia. Al
enchufarlos apareció `test_base_lib.py` en rojo desde que `en_carpeta()` exige
la carpeta absoluta: nadie lo sabía.

Lo que sigue abierto: **la lista es manual**. Un repo nuevo no entra solo, y
nada avisa de que falta — el mismo modo de fallo, un nivel más arriba.""", "1")
L.nodo("d_sin_bases", C["compuertas"], YD, L.ancho, 360, """## 🟥 el sistema no tabula sus **propias piezas**
Este wiki repo publica **1 Base**: el histórico de sus diseños, que
`generar_versiones.py` genera solo. Las siete piezas, sus versiones y qué
repo consume cada una **no** están tabuladas.

No es olvido: `base_lib` rechaza en **duro** una columna que ninguna nota
declare, así que hace falta antes una nota por pieza. Ése es el trabajo que
falta, y se **nombra** en vez de rellenarse — la misma regla que rige cada
cifra de este mapa.""", "1")
L.nodo("d_dos_raices", C["boveda"], YD, L.ancho, 340, """## 🟥 hay dos bóvedas anidadas (INC-003)
`/mnt/f/OBSIDIAN` y `/mnt/f/OBSIDIAN/wiki` tienen las dos su `.obsidian/`.

Cada `.base` publica hoy un `or` sobre las dos raíces, y eso **es**
información: dice que este disco tiene más de una bóveda. Pero la causa sigue
abierta, y cualquier ruta escrita a mano puede volver a fallar en el único modo
que importa: **en silencio y con la tabla en blanco**.""", "1")
L.nodo("d_comas", C["humano"], YD, L.ancho, 340, """## 🟥 el frontmatter parte las listas por comas
`bloqueado_por: ["[[Una nota, con coma]]"]` pierde el enlace y no lo dice.

Ya obligó a declarar **un** bloqueante en INC-014 donde había dos. Es
exactamente la clase de fallo que esta arquitectura existe para no tener:
silencioso, y con el dato mal en la cara de quien lo lee.""", "1")
L.envolver("g_deuda", "LO QUE HOY NO CIERRA — dibujado igual de grande que lo que funciona",
           ["d_consumidor", "d_sin_bases", "d_dos_raices", "d_comas"], color="1")
# ── aristas ────────────────────────────────────────────────────────────────
L.arista("r_manifiesto", "c_legible", "right", "left", "qué hay que publicar")
L.arista("r_generadores", "c_legible", "right", "left", "el canvas, antes de escribirlo")
L.arista("r_piezas", "c_base", "right", "left", "quién mide")
L.arista("c_legible", "b_mapas", "right", "left", "pasa ⇒ se escribe")
L.arista("c_base", "b_bases", "right", "left", "pasa ⇒ se publica")
L.arista("c_indexado", "b_puerta", "right", "left", "o no se publica nada")
L.arista("c_no_pisar", "b_incidencias", "right", "left", "lo tuyo se queda")
L.arista("c_archivo", "b_versiones", "right", "left", "lo de ayer se guarda")
L.arista("b_mapas", "h_lee", "right", "left", "se abre en Obsidian")
L.arista("b_incidencias", "h_edita", "right", "left", "se escribe a mano")
L.arista("h_edita", "h_adopta", "bottom", "top", "¿esto pasa a ser la verdad?")
L.arista("h_adopta", "v_adopta", "bottom", "right", "sí ⇒ se adopta")
L.arista("h_declara", "v_declara", "bottom", "right", "y el diseño se reescribe")
L.arista("v_adopta", "r_lock", "left", "bottom")
L.arista("v_declara", "r_manifiesto", "left", "bottom")
L.arista("r_lock", "c_no_pisar", "right", "left", "compara: repo vs bóveda")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else str(
        Path(__file__).resolve().parent / "el_wiki_repo.canvas")
    ok, lineas = informe(L.a_dict(), libres={"leyenda", "tesis"})
    for l in lineas:
        print("  " + l)
    if not ok:
        raise SystemExit("✗ no se escribe un canvas con etiquetas ilegibles")
    print(f"  ✓ {L.escribir(out)}")
