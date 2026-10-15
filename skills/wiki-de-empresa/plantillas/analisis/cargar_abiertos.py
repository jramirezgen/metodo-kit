"""Carga las series abiertas descargadas (BCRP) y su manifiesto de fuentes en el almacén.

    python3 analisis/dwh/cargar_abiertos.py <almacen.sqlite> [<carpeta_abiertos>]

Falla si el formato de la API cambia; no adivina. Idempotente: reemplaza lo anterior de cada serie.
"""
import hashlib
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ABIERTOS = Path("/mnt/f/db/sapyria/abiertos")
MESES = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}
MESES.update({"Ene": 1, "Abr": 4, "Ago": 8, "Set": 9, "Dic": 12})   # la API del BCRP mezcla: «Set» aparece en las series reales
ESQUEMA = """
CREATE TABLE IF NOT EXISTS ref_fuente (archivo TEXT PRIMARY KEY, sha256 TEXT NOT NULL, cargado_en TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS ref_tipo_cambio (fecha TEXT PRIMARY KEY, pen_por_usd REAL NOT NULL);
CREATE TABLE IF NOT EXISTS ref_ipc_lima (periodo TEXT PRIMARY KEY, var_mensual_pct REAL NOT NULL);
"""


def _periodos(ruta: Path):
    d = json.loads(ruta.read_text(encoding="utf-8"))
    if "periods" not in d or not all("name" in p and "values" in p for p in d["periods"]):
        raise ValueError(f"{ruta.name}: formato de la API distinto del esperado")
    return d["periods"]


def _valor(p):
    v = p["values"][0]
    return None if v == "n.d." else float(v)


def fecha_diaria(nombre: str) -> str:
    m = re.fullmatch(r"(\d{2})\.([A-Za-z]{3})\.(\d{2})", nombre)
    if not m:
        raise ValueError(f"fecha diaria no reconocida: {nombre}")
    return f"20{m[3]}-{MESES[m[2]]:02d}-{m[1]}"


def periodo_mensual(nombre: str) -> str:
    m = re.fullmatch(r"([A-Za-z]{3})\.(\d{4})", nombre)
    if not m:
        raise ValueError(f"periodo mensual no reconocido: {nombre}")
    return f"{m[2]}-{MESES[m[1]]:02d}"


def cargar(con: sqlite3.Connection, abiertos: Path = ABIERTOS) -> dict:
    con.executescript(ESQUEMA)
    tc = [(fecha_diaria(p["name"]), _valor(p)) for p in _periodos(abiertos / "bcrp/tc_venta_PD04638PD.json")]
    tc = [(f, v) for f, v in tc if v is not None]
    ipc = [(periodo_mensual(p["name"]), _valor(p)) for p in _periodos(abiertos / "bcrp/ipc_lima_var_mensual_PN01271PM.json")]
    ipc = [(f, v) for f, v in ipc if v is not None]
    con.execute("DELETE FROM ref_tipo_cambio"); con.execute("DELETE FROM ref_ipc_lima")
    con.executemany("INSERT INTO ref_tipo_cambio VALUES (?,?)", tc)
    con.executemany("INSERT INTO ref_ipc_lima VALUES (?,?)", ipc)
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for f in sorted(p for p in abiertos.rglob("*") if p.is_file() and p.name != "MANIFIESTO.sha256"):
        con.execute("INSERT OR REPLACE INTO ref_fuente VALUES (?,?,?)",
                    (str(f.relative_to(abiertos)), hashlib.sha256(f.read_bytes()).hexdigest(), ahora))
    con.commit()
    return {"tipo_cambio": len(tc), "ipc": len(ipc), "fuentes": con.execute("SELECT count(*) FROM ref_fuente").fetchone()[0]}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    print(cargar(sqlite3.connect(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else ABIERTOS))
