-- Modelo mínimo CRM + ERP + data warehouse. SIN datos de identidad: solo seudónimos.
-- construir_dwh.py rechaza cualquier columna cuyo nombre sugiera identidad.
PRAGMA foreign_keys = ON;
CREATE TABLE dim_tiempo (fecha TEXT PRIMARY KEY, anio INTEGER, mes INTEGER, trimestre INTEGER);
CREATE TABLE dim_producto (producto_id TEXT PRIMARY KEY, descripcion TEXT NOT NULL);
CREATE TABLE dim_canal (canal_id TEXT PRIMARY KEY, descripcion TEXT NOT NULL);
CREATE TABLE crm_aliado (aliado_id TEXT PRIMARY KEY CHECK (aliado_id GLOB 'MED-[0-9][0-9][0-9]' OR aliado_id GLOB 'EST-[0-9][0-9][0-9]'), tipo TEXT NOT NULL, canal_id TEXT REFERENCES dim_canal);
CREATE TABLE crm_pedido (pedido_id TEXT PRIMARY KEY CHECK (pedido_id GLOB 'C-[0-9][0-9][0-9][0-9]'), aliado_id TEXT REFERENCES crm_aliado, canal_id TEXT REFERENCES dim_canal, etapa TEXT NOT NULL, fecha_alta TEXT REFERENCES dim_tiempo);
CREATE TABLE erp_linea (pedido_id TEXT REFERENCES crm_pedido, producto_id TEXT REFERENCES dim_producto, precio_sin_igv REAL NOT NULL, costo_variable REAL, PRIMARY KEY (pedido_id, producto_id));
CREATE TABLE erp_pago (pago_id INTEGER PRIMARY KEY, pedido_id TEXT REFERENCES crm_pedido, fecha TEXT REFERENCES dim_tiempo, monto REAL NOT NULL, concepto TEXT NOT NULL);
CREATE TABLE erp_compra (compra_id INTEGER PRIMARY KEY, proveedor TEXT NOT NULL, fecha TEXT REFERENCES dim_tiempo, monto_usd REAL NOT NULL, retencion REAL DEFAULT 0, igv_utilizacion REAL DEFAULT 0);
CREATE VIEW kpi_ingresos_mes AS SELECT substr(fecha,1,7) AS mes, SUM(monto) AS ingresos FROM erp_pago GROUP BY 1;
CREATE VIEW kpi_margen_pedido AS SELECT pedido_id, SUM(precio_sin_igv) AS ingreso, SUM(costo_variable) AS costo, SUM(precio_sin_igv) - SUM(costo_variable) AS margen FROM erp_linea GROUP BY 1;
CREATE VIEW kpi_conversion AS SELECT etapa, COUNT(*) AS pedidos FROM crm_pedido GROUP BY 1;
