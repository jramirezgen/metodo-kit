# JSON Canvas 1.0 — el formato entero, en una página

Especificación abierta que usa Obsidian para los `.canvas`. Un fichero es un
único objeto JSON con dos listas.

```json
{ "nodes": [ … ], "edges": [ … ] }
```

## Nodos — lo común a los cuatro tipos

| campo | tipo | obligatorio | qué es |
|---|---|---|---|
| `id` | string | sí | único en el fichero |
| `type` | string | sí | `text` · `file` · `link` · `group` |
| `x`, `y` | integer | sí | esquina superior izquierda, en píxeles |
| `width`, `height` | integer | sí | tamaño en píxeles |
| `color` | string | no | `"1"`–`"6"` o un hex `"#ff0000"` |

**Los seis colores nombrados:** `1` rojo · `2` naranja · `3` amarillo ·
`4` verde · `5` cian · `6` morado.

| tipo | campo propio | contenido |
|---|---|---|
| `text` | `text` | Markdown. Tablas, código y emoji se renderizan |
| `file` | `file` (+ `subpath` opcional) | ruta a un fichero del vault; `subpath` es un `#encabezado` o `#^bloque` |
| `link` | `url` | una URL |
| `group` | `label`, `background`, `backgroundStyle` | rectángulo que agrupa; `backgroundStyle` ∈ `cover` · `ratio` · `repeat` |

## Aristas

| campo | tipo | obligatorio | qué es |
|---|---|---|---|
| `id` | string | sí | único |
| `fromNode`, `toNode` | string | sí | `id` de un nodo existente |
| `fromSide`, `toSide` | string | no | `top` · `right` · `bottom` · `left` |
| `fromEnd`, `toEnd` | string | no | `none` · `arrow` (por defecto: `none` en el origen, `arrow` en el destino) |
| `color` | string | no | igual que en los nodos |
| `label` | string | no | **el texto que se dibuja en medio de la flecha** |

## Lo que la especificación NO dice, y hay que saber

- **La pertenencia a un grupo es geométrica.** No existe un campo «hijos»: un
  nodo está en un grupo si cae dentro de su rectángulo. Mover el grupo arrastra
  lo que contiene, así que **dos grupos no pueden solaparse a medias** —
  anidarse sí.
- **La etiqueta de una arista es una caja, no un punto.** Se dibuja centrada en
  el punto medio de la curva. Para una bezier cúbica con tiradores horizontales
  ese punto medio es **exactamente la media de las dos anclas**:
  `(P₀ + 3(P₀+d) + 3(P₃−d) + P₃)/8 = (P₀+P₃)/2`. Medido en la fuente por
  defecto: ≈ **7,5 px por carácter** y **26 px** de alto.
- **No hay z-index.** Si la caja de una etiqueta cae sobre un nodo, se pierde.
  El único remedio es geometría: corredor ancho entre columnas.
- **No hay layout automático.** Las coordenadas son absolutas y en píxeles; el
  orden de la lista no importa.
- **Obsidian no abre un `.canvas` que vive fuera de la bóveda.** En WSL eso
  significa que el fichero tiene que estar bajo `/mnt/f/OBSIDIAN/`, no en el
  árbol del repo.

Fuente: <https://jsoncanvas.org/spec/1.0/> (especificación 1.0, MIT).
