"""Exporta las constantes numéricas de un módulo de supuestos a supuestos.json (MATLAB y R lo leen).

    python3 analisis/exportar_supuestos.py <modulo.py> [salida.json]
"""
import importlib.util
import json
import sys
from pathlib import Path


def exportar(modulo: Path, salida: Path) -> dict:
    spec = importlib.util.spec_from_file_location("supuestos", modulo)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    datos = {k: v for k, v in vars(m).items()
             if k.isupper() and isinstance(v, (int, float, str, list, dict, tuple))}
    salida.write_text(json.dumps(datos, ensure_ascii=False, indent=1, default=list) + "\n", encoding="utf-8")
    return datos


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    s = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("analisis/salidas/supuestos.json")
    s.parent.mkdir(parents=True, exist_ok=True)
    print(f"✓ {len(exportar(Path(sys.argv[1]), s))} supuestos → {s}")
