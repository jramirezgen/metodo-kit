# -*- coding: utf-8 -*-
"""La política `archivar: estructura`: el texto solo no archiva; nodos y aristas sí."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import archivar as A  # noqa: E402

def cv(nodos, aristas=()):
    return json.dumps({"nodes": [{"id": i, "type": "text", "text": t} for i, t in nodos],
                       "edges": [{"id": f"{a}{b}", "fromNode": a, "toNode": b} for a, b in aristas]})

base = cv([("a", "x"), ("b", "y")], [("a", "b")])
fallos = 0
def caso(nombre, cond):
    global fallos
    print(("  ✓ " if cond else "  ✗ ") + nombre)
    fallos += not cond

print("archivar — política estructural")
caso("cambia sólo un texto: no es estructural", not A.es_estructural(base, cv([("a", "x2"), ("b", "y")], [("a", "b")])))
caso("nace un nodo: es estructural", A.es_estructural(base, cv([("a", "x"), ("b", "y"), ("c", "z")], [("a", "b")])))
caso("cambia una arista: es estructural", A.es_estructural(base, cv([("a", "x"), ("b", "y")], [("b", "a")])))
caso("un canvas ilegible cuenta como estructural", A.es_estructural("{no json", base))

with tempfile.TemporaryDirectory() as d:
    d = Path(d); dest = d / "m.canvas"; dest.write_text(base)
    item = {"n": 1, "titulo": "Mapa"}
    nuevo = cv([("a", "x2"), ("b", "y")], [("a", "b")])
    caso("solo_estructura=True no archiva un cambio de texto",
         A.archivar(dest, nuevo, item, d / "V", 1, {}, solo_estructura=True) is None)
    caso("por defecto sigue archivando todo",
         A.archivar(dest, nuevo, item, d / "V", 1, {}) is not None)

print(f"\n{'✗ ' + str(fallos) + ' fallo(s)' if fallos else 'verde'}")
sys.exit(1 if fallos else 0)
