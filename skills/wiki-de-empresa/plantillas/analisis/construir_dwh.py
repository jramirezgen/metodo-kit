"""Construye el data warehouse mínimo desde SI1_ESQUEMA.sql y verifica que no entra identidad.

    python3 analisis/dwh/construir_dwh.py <ruta.sqlite> [--ejemplo]

--ejemplo carga filas sintéticas para probar las vistas de KPI. Sin dependencias fuera de la biblioteca estándar.
"""
import re
import sqlite3
import sys
from pathlib import Path

ESQUEMA = Path(__file__).resolve().parents[2] / "docs" / "empresa" / "sistemas" / "SI1_ESQUEMA.sql"
IDENTIDAD = re.compile(r"nombre|apellido|dni|pasaporte|email|correo|telefono|celular|direccion|ruc_persona", re.I)


def columnas_con_identidad(con: sqlite3.Connection) -> list[str]:
    malas = []
    for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')"):
        for c in con.execute(f"PRAGMA table_info({t})"):
            if IDENTIDAD.search(c[1]):
                malas.append(f"{t}.{c[1]}")
    return malas


def construir(destino: str, ejemplo: bool = False) -> sqlite3.Connection:
    con = sqlite3.connect(destino)
    con.executescript(ESQUEMA.read_text(encoding="utf-8"))
    malas = columnas_con_identidad(con)
    if malas:
        raise SystemExit(f"✗ columnas con identidad: {malas}")
    if ejemplo:
        con.executescript("""
        INSERT INTO dim_tiempo VALUES ('2026-10-12',2026,10,4);
        INSERT INTO dim_producto VALUES ('P1','producto de ejemplo');
        INSERT INTO dim_canal VALUES ('K1','canal de ejemplo');
        INSERT INTO crm_aliado VALUES ('MED-001','medico','K1');
        INSERT INTO crm_pedido VALUES ('C-0001','MED-001','K1','cotizado','2026-10-12');
        INSERT INTO erp_linea VALUES ('C-0001','P1',100,60);
        INSERT INTO erp_pago(pedido_id,fecha,monto,concepto) VALUES ('C-0001','2026-10-12',50,'inicial');
        """)
        con.commit()
    return con


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    c = construir(sys.argv[1], "--ejemplo" in sys.argv)
    print("✓ almacén construido; KPI:", c.execute("SELECT * FROM kpi_margen_pedido").fetchall())
