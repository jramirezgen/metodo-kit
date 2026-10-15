# Sistemas: CRM, ERP mínimo y data warehouse de {empresa} (nodo SI0)

Estado: {fecha}.

> POR COMPLETAR

## Responsabilidades
| Sistema | Responde a | Clave | Datos de identidad |
|---|---|---|---|
| CRM | ¿quién es el cliente/aliado y en qué punto del ciclo está? | seudónimo (`C-NNNN`, `MED-NNN`) | expediente privado fuera de git |
| ERP mínimo | ¿qué se cotizó, compró, facturó y cobró, y qué impuesto genera? | pedido | no |
| Data warehouse | ¿cómo va el negocio? (KPI) | estrella: hechos y dimensiones | nunca |

## Decisiones a escribir
- Umbral de volumen a partir del cual se compra o instala un producto (CRM/ERP) y cuál sería; hasta entonces, tablas y vistas sobre el registro.
- Qué NO se pone todavía y por qué; cómo se revertiría.
- Fuentes del ETL, frecuencia, y quién lee el almacén (R y MATLAB, solo lectura).

## Mapa de capas (cada fila: sitio + regla de imports + prueba)
| Capa | Pregunta | Sitio | Regla | Prueba |
|---|---|---|---|---|
| Presentación | ¿formatear la salida está separado de orquestar? | | | |
| API pública | ¿hay fachada estable y la CLI es un cliente más? | | | |
| Aplicación | ¿los casos de uso y el pipeline tienen capa propia? | | | |
| Dominio | ¿es puro: sin I/O, reloj ni configuración? | | | |
| Datos | ¿esquema versionado, claves seudónimas, constraint anti-identidad? | | | |
| Integración | ¿cada sistema externo pasa por un adaptador con política de red y contract test? | | | |
| Transversales | ver SI3 (siete) | | | |

El dominio **nunca** importa lo transversal: le llega por puertos o ya validado.
