#!/usr/bin/env python3
"""Servidor MCP sobre el motor de consulta.py — mismo cerebro, interfaz tipada.

No reimplementa nada: importa consulta.py (léxico ponderado + difusión de un
salto por el grafo de `wiki/` + presupuesto de tokens en dos bolsas, ya afinado
empíricamente — ver los comentarios fechados en ese archivo) y lo expone como
tool calls de MCP en vez de un comando de shell con flags que hay que recordar.

Por qué existe: los MCP `server-filesystem` ya conectados (`obsidian-vault`,
`obsidian-jeanne`) son el paquete genérico de referencia de Anthropic apuntado
a carpetas del vault. No hablan el grafo de `[[enlaces]]`, no tienen
presupuesto de tokens y no distinguen procedencia léxico/grafo — exactamente
las tres garantías que la Regla 3 del protocolo del vault exige. Este servidor
no los reemplaza (siguen siendo la vía de escritura de notas nuevas); cubre la
LECTURA con las mismas garantías que `consulta.py` ya tenía por CLI, sin la
fricción de invocar Bash y memorizar flags.

Uso (registrado como MCP stdio, ver `claude mcp add`):
    python3 mcp_server.py
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import consulta  # noqa: E402 (después de tocar sys.path)

from mcp.server.mcpserver import MCPServer  # noqa: E402

RAIZ = consulta.RAIZ_POR_DEFECTO

server = MCPServer(
    name="vault-consulta",
    version="1.0.0",
    instructions=(
        "Busca en el segundo cerebro (wiki/ + alejandria/ de /mnt/f/OBSIDIAN) "
        "dentro de un presupuesto de tokens fijo, recorriendo el grafo de "
        "enlaces curados de wiki/. Preferir esto sobre leer archivos sueltos "
        "del vault: nunca barrer wiki/ ni alejandria/ a mano — para eso están "
        "las reglas del CLAUDE.md del vault."
    ),
)


@server.tool()
def buscar_vault(consulta_texto: str, k: int = 5, tokens: int = 1200,
                  sin_grafo: bool = False) -> dict:
    """Busca en wiki/ y alejandria/: léxico ponderado por ubicación + un salto
    de grafo por los enlaces curados de wiki/.

    Devuelve fragmentos por SECCIÓN (no notas enteras) con procedencia — "via":
    "lexico" o "grafo", y "enlazado_desde" cuando llegó por el grafo. El
    presupuesto de salida (`tokens`, por defecto 1200) se reparte entre
    aciertos directos y los traídos por el grafo, así que nunca crece sin
    control. `k` es el máximo de documentos distintos (por defecto 5).
    `sin_grafo=True` desactiva la difusión y deja solo emparejamiento léxico.

    El emparejamiento es LÉXICO: usar términos del dominio ("tilt ambiental",
    "MECATE", "Y_G"), no prosa libre — una pregunta completa en español pierde
    precisión frente a los términos exactos que usan las notas.
    """
    docs = consulta.cargar(RAIZ)
    resultados = consulta.buscar(docs, consulta_texto, k, tokens,
                                  difundir=not sin_grafo)
    return {"consulta": consulta_texto, "resultados": resultados}


@server.tool()
def nota_vault(titulo: str) -> str:
    """Devuelve el texto COMPLETO de una nota de wiki/ o un documento de
    alejandria/, por su título exacto (acentos/mayúsculas no importan).

    Usar solo cuando ya se sabe qué nota hace falta entera — la señaló
    `buscar_vault`, `index.md` o `alejandria/INDICE.md`. Para explorar o no
    saber qué existe, usar `buscar_vault` primero: abrir una nota de
    alejandria/ cuesta 2 000–17 000 tokens.
    """
    for d in consulta.cargar(RAIZ):
        if consulta.normalizar(d["titulo"]) == consulta.normalizar(titulo):
            return (RAIZ / d["ruta"]).read_text(encoding="utf-8")
    raise ValueError(f"No existe la nota «{titulo}».")


@server.tool()
def mapa_vault() -> dict:
    """Costo en tokens de `index.md` y `alejandria/INDICE.md`, sin abrir
    ninguno de los dos. Consultar esto antes de decidir si hace falta abrir
    el índice temático completo en vez de seguir con `buscar_vault`.
    """
    return consulta.mapa(RAIZ)


if __name__ == "__main__":
    server.run()
