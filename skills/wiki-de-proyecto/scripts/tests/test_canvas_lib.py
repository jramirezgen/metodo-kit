#!/usr/bin/env python3
"""La compuerta de etiquetas es binaria, y por eso no avisa de nada.

⛔ **El defecto, medido el 2026-09-08 al compactar `apolo_lazo_de_control`.**
`validar` dice «tapada» o no dice nada. Es un acantilado: con paso de columna
**810 px** el canvas sale verde y con **800 px** salen dos etiquetas tapadas.
Diez píxeles separan «perfecto» de «roto», y desde dentro del verde no hay forma
de saber a qué distancia del borde se está.

Eso importa porque el canvas se **edita**: se le cambia el texto a una arista y
la etiqueta crece. Con 592 px de margen no pasa nada; con 52, la siguiente
palabra la tapa — y el generador se negará a escribir sin haber avisado ni una
vez de que el sitio se estaba acabando.

Así que junto a la regla dura va una blanda: **cuánto puede crecer todavía cada
etiqueta antes de tocar un nodo**. Es la misma pareja que ya usa el resto del
módulo (duro = no se escribe, aviso = se dice y se sigue), y es lo que convierte
«mide 940 y funciona» en «mide 940 y le quedan 132 px».

Uso: python3 scripts/tests/test_canvas_lib.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import canvas_lib as CL  # noqa: E402


def ok(titulo: str, condicion: bool, detalle: str = "") -> bool:
    print(f"  {'✓' if condicion else '✗'} {titulo}"
          + (f" → {detalle}" if detalle and not condicion else ""))
    return condicion


def lienzo(separacion: int, etiqueta: str) -> dict:
    """Dos nodos en la misma fila, con una arista rotulada entre ellos."""
    return {
        "nodes": [
            {"id": "a", "type": "text", "x": 0, "y": 0,
             "width": 620, "height": 200, "text": "a"},
            {"id": "b", "type": "text", "x": 620 + separacion, "y": 0,
             "width": 620, "height": 200, "text": "b"},
        ],
        "edges": [{"id": "e1", "fromNode": "a", "fromSide": "right",
                   "toNode": "b", "toSide": "left", "label": etiqueta}],
    }


def problemas(canvas: dict, clase: str) -> list:
    return [p for p in CL.validar(canvas, exigir_grupo=False)
            if p.regla.startswith(clase)]


def caso_el_aviso_llega_antes_que_el_fallo() -> list[bool]:
    print("margen — el aviso salta ANTES de que la etiqueta se tape")
    corto = "x"                       # 7,5 px: le sobra sitio
    largo = "y de aquí sale el trabajo"   # 187 px, la más ancha de APOLO hoy
    ancho = len(largo) * CL.PX_POR_CARACTER
    # Separación tal que a la etiqueta le quedan ~40 px: no toca, pero ya no cabe
    justo = int((ancho + 40) / 2) * 2
    return [
        ok("con sitio de sobra no dice nada",
           not problemas(lienzo(2000, largo), "etiqueta")),
        ok("sin sitio sigue siendo un fallo DURO",
           any(p.duro for p in problemas(lienzo(100, largo), "etiqueta tapada"))),
        ok("a punto de taparse avisa, y NO bloquea",
           [p.duro for p in problemas(lienzo(justo, largo), "etiqueta sin margen")]
           == [False],
           f"{[str(p) for p in problemas(lienzo(justo, largo), 'etiqueta')]}"),
        ok("el aviso nombra los píxeles que quedan",
           any("px" in str(p)
               for p in problemas(lienzo(justo, largo), "etiqueta sin margen"))),
        ok("una etiqueta corta en el mismo hueco no avisa",
           not problemas(lienzo(justo, corto), "etiqueta")),
    ]


def caso_los_canvas_reales_nacen_verdes() -> list[bool]:
    """Una compuerta que nace roja se aprende a ignorar: se comprueba antes."""
    print("\nmargen — los canvas ya publicados no encienden el aviso nuevo")
    repo = Path("/home/kaitokid/Documents/REPOSITORIOS/element/docs/wiki")
    if not repo.is_dir():
        print("  ⚠ el repo consumidor no está: caso NO comprobado")
        return []
    import json
    r = []
    for nombre in sorted(repo.glob("*.canvas")):
        canvas = json.loads(nombre.read_text(encoding="utf-8"))
        avisos = problemas(canvas, "etiqueta sin margen")
        r.append(ok(f"{nombre.name}", not avisos,
                    "; ".join(str(p) for p in avisos)))
    return r


def main() -> int:
    r = caso_el_aviso_llega_antes_que_el_fallo() + caso_los_canvas_reales_nacen_verdes()
    print(f"\n{sum(r)}/{len(r)} verde")
    return 0 if all(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
