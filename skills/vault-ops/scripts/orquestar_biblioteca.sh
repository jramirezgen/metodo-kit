#!/usr/bin/env bash
# Orquestador determinista del pipeline de la bibliotecaria: triaje -> alta en
# Alejandría -> catálogo -> extracción (bibliotecaria) -> certificación.
#
# NO es un agente ni pasa por un LLM: encadenar pasos ya deterministas no es
# una tarea de juicio, es un if/then. Meter un agente acá violaría el propio
# principio del stack — "el modelo propone, las reglas disponen" — sin ganar
# nada (más costo, más latencia, una fuente nueva de fallo). Los ÚNICOS lugares
# donde el 9B decide algo siguen siendo triaje.py y bibliotecaria.py, cada uno
# ya con su compuerta de verificación mecánica.
#
# Deliberadamente SIN cron/systemd timer todavía: se invoca a mano hasta que
# corra limpio a escala completa unas cuantas veces. Ver
# wiki/SISTEMA/Amadeus — el segundo cerebro como backend.md.
#
# Uso:
#   bash orquestar_biblioteca.sh              # corrida completa
#   bash orquestar_biblioteca.sh --n 20        # limita bibliotecaria a 20 (prueba)
set -euo pipefail

RAIZ_VAULT="/mnt/f/OBSIDIAN"
SCRIPTS="/mnt/f/skills/_personales/vault-ops/scripts"
PAUSE_FLAG="$HOME/.local/state/amadeus/PAUSED"
STOP_FLAG="$HOME/.local/state/amadeus/STOP"
MAX_WAIT_SEC=1800
POLL_SEC=30
LOG="$HOME/.local/state/amadeus/orquestador.log"
UMBRAL_ALUCINACION=35   # % — por encima de esto, para y avisa en vez de seguir

N_BIBLIOTECARIA="0"
if [ "${1:-}" = "--n" ]; then
  N_BIBLIOTECARIA="$2"
fi

log() {
  mkdir -p "$(dirname "$LOG")"
  echo "$(date '+%Y-%m-%d %H:%M:%S') $*" | tee -a "$LOG"
}

abortar_si_stop() {
  # Parada dura (kill switch), distinta de la pausa cooperativa de arriba:
  # no espera ni reintenta, corta el pipeline de inmediato.
  if [ -f "$STOP_FLAG" ]; then
    log "ABORTADO: STOP detectado ($STOP_FLAG)"
    exit 90
  fi
}

esperar_si_pausado() {
  abortar_si_stop
  local esperado=0
  while [ -f "$PAUSE_FLAG" ]; do
    abortar_si_stop   # no quedarse atascado hasta MAX_WAIT_SEC si aparece STOP en pausa
    if [ "$esperado" -eq 0 ]; then
      log "en pausa: $(cat "$PAUSE_FLAG")"
    fi
    if [ "$esperado" -ge "$MAX_WAIT_SEC" ]; then
      log "ABORTADO: pausa excedió ${MAX_WAIT_SEC}s"
      exit 75
    fi
    sleep "$POLL_SEC"
    esperado=$((esperado + POLL_SEC))
  done
}

paso() {
  local nombre="$1"; shift
  esperar_si_pausado
  log "-> $nombre"
  if ! "$@" 2>&1 | tee -a "$LOG"; then
    log "FALLÓ: $nombre — abortando el resto del pipeline"
    exit 1
  fi
}

abortar_si_stop
log "=== inicio corrida ==="

paso "triaje: clasificar pendientes" \
  python3 "$SCRIPTS/triaje.py" --n 0

paso "triaje: aplicar (mover RUIDO a descarte)" \
  python3 "$SCRIPTS/triaje.py" --aplicar

paso "alejandria: alta de candidatos" \
  python3 "$SCRIPTS/alejandria_intake.py" "$RAIZ_VAULT" --aplicar

paso "alejandria: regenerar catálogo" \
  python3 "$SCRIPTS/alejandria_index.py" "$RAIZ_VAULT" --escribir

esperar_si_pausado
log "-> bibliotecaria: extraer (n=$N_BIBLIOTECARIA)"
python3 "$SCRIPTS/bibliotecaria.py" --n "$N_BIBLIOTECARIA" 2>&1 | tee -a "$LOG"

# Compuerta de calidad: leer la tasa de alucinación del informe y decidir con
# un número, no con impresión. Si se disparó respecto al 20% medido en el
# prototipo, frenar ahí — no seguir generando borradores potencialmente malos.
informe="$(python3 "$SCRIPTS/bibliotecaria.py" --informe 2>&1)"
echo "$informe" | tee -a "$LOG"
tasa="$(echo "$informe" | grep -oP 'tasa de alucinación: \K[0-9.]+' || echo 0)"
if awk "BEGIN{exit !($tasa > $UMBRAL_ALUCINACION)}"; then
  log "ALERTA: tasa de alucinación ${tasa}% > umbral ${UMBRAL_ALUCINACION}% — revisar antes de confiar en los borradores nuevos"
fi

esperar_si_pausado
log "-> certificación del vault (informativo: fallas preexistentes no son de este pipeline)"
if bash "$SCRIPTS/certificar.sh" "$RAIZ_VAULT" 2>&1 | tee -a "$LOG"; then
  log "certificación: PASA"
else
  log "certificación: hay fallas — revisar arriba si son nuevas o ya conocidas"
fi

log "=== fin corrida ==="
