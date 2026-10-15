# Estadística descriptiva de entrevistas o ventas: lee CSV de analisis/salidas/. Sin cifras tecleadas.
# Uso: Rscript analisis/r/resumen.R   (requiere solo jsonlite; ggplot2/data.table si están)
suppressWarnings(library(jsonlite))
s <- fromJSON("analisis/salidas/supuestos.json")
str(s, max.level = 1)
