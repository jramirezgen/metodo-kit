#!/usr/bin/env bash
# Compuerta única del segundo cerebro. Falla si el sistema no está sano.
#
# Es el análogo de `element/tools/preflight.py`: los documentos pasivos no
# cambian la conducta, un comando que falla sí. Correr antes de dar por buena una
# tanda de ediciones y antes de decir que el sistema "está bien".
#
# Uso:  bash certificar.sh [raiz_vault]
# Sale con 0 solo si TODOS los invariantes se cumplen.

set -uo pipefail
RAIZ="${1:-/mnt/f/OBSIDIAN}"
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FALLOS=0

titulo() { printf '\n\033[1m== %s\033[0m\n' "$1"; }
ok()     { printf '  \033[32mPASA\033[0m  %s\n' "$1"; }
mal()    { printf '  \033[31mFALLA\033[0m %s\n' "$1"; FALLOS=$((FALLOS+1)); }

printf '\033[1mCERTIFICACIÓN DEL SEGUNDO CEREBRO\033[0m — %s\n' "$(date '+%Y-%m-%d %H:%M')"
printf 'Vault: %s\n' "$RAIZ"

titulo "1. Integridad estructural"
if python3 "$AQUI/vault_audit.py" "$RAIZ" --ci; then
  ok "sin enlaces rotos, frontmatter e índice completos, sin islas ni bóvedas anidadas"
else
  mal "el vault viola algún invariante estructural (detalle arriba)"
fi

titulo "2. Catálogo de Alejandría"
# Ojo: `$?` tras una ASIGNACIÓN devuelve el estado de la asignación, no el del
# comando. Hay que capturarlo en la misma línea.
SAL_AL="$(python3 "$AQUI/alejandria_index.py" "$RAIZ" --escribir 2>&1)"; RC_AL=$?
# Un documento sin `resumen` es ininvocable: es fallo, no aviso.
HUERF="$(grep -oP '\d+(?= sin catalogar)' <<<"$SAL_AL" | head -1)"
HUERF="${HUERF:-0}"
if [ "$RC_AL" -ne 0 ]; then
  mal "el catálogo no se pudo generar: $SAL_AL"
elif [ "$HUERF" -ne 0 ]; then
  mal "$HUERF documentos sin \`al\` o sin \`resumen\` — son ininvocables"
else
  ok "$(sed 's/^catálogo -> //' <<<"$SAL_AL")"
fi

titulo "3. Coherencia epistémica (cifras canónicas)"
# El veredicto lo da el CÓDIGO DE SALIDA, no el texto: claim_lint sale 1 solo
# si hay contradicciones VIGENTES. Las de notas con `registro_historico: true`
# se listan en su propia sección y no bloquean — una bitácora cita la cifra que
# se reportó en su día, y prohibírselo sería reescribir la historia.
SAL_LINT="$(python3 "$AQUI/claim_lint.py" "$RAIZ" 2>&1)"; LINT_RC=$?
HIST="$(grep -o '[0-9]* en registros históricos' <<<"$SAL_LINT" | head -1)"
if [ "$LINT_RC" -eq 0 ]; then
  ok "$(grep -o '[0-9]* cifras canónicas vigiladas' <<<"$SAL_LINT" | head -1), 0 contradicciones vigentes${HIST:+ (${HIST}, no bloquean)}"
else
  mal "$(grep -o '[0-9]* líneas contradicen.*' <<<"$SAL_LINT" | head -1)"
  # Solo las bloqueantes: la tabla histórica viene tras su propio encabezado `## `.
  sed -n '/líneas contradicen/,/^## /p' <<<"$SAL_LINT" | grep '^| `' | head -5
  [ -n "$HIST" ] && echo "        (además, $HIST — no bloquean)"
fi

titulo "4. Backend de consulta (lo que usa el agente local)"
SAL_Q="$(python3 "$AQUI/consulta.py" "autoridad epistemica" --tokens 400 --k 2 2>&1)"
if grep -q "^## " <<<"$SAL_Q"; then
  ok "responde con fragmentos ($(grep -c '^## ' <<<"$SAL_Q") secciones, ~$(grep -oP '~\K[0-9]+(?= tokens)' <<<"$SAL_Q" | head -1) tokens)"
else
  mal "el backend no devuelve fragmentos: $(head -2 <<<"$SAL_Q")"
fi

titulo "5. Respaldo en disco distinto"
SELLO="/mnt/g/BACKUP_SEGUNDO_CEREBRO/ULTIMO_RESPALDO.txt"
if [ -f "$SELLO" ]; then
  EDAD_H=$(( ( $(date +%s) - $(stat -c %Y "$SELLO") ) / 3600 ))
  if [ "$EDAD_H" -le 24 ]; then
    ok "respaldo de hace ${EDAD_H} h en G: — $(head -2 "$SELLO" | tail -1)"
  else
    mal "el respaldo tiene ${EDAD_H} h de antigüedad (umbral: 24 h). Corre respaldo.ps1"
  fi
else
  mal "NO HAY RESPALDO en otro disco. Corre respaldo.ps1 — es el único fallo sin vuelta atrás"
fi

titulo "6. Historial de versiones"
if git -C "$RAIZ" rev-parse --git-dir >/dev/null 2>&1; then
  SUCIO="$(git -C "$RAIZ" status --porcelain | wc -l)"
  N="$(git -C "$RAIZ" rev-list --count HEAD 2>/dev/null || echo 0)"
  if [ "$SUCIO" -eq 0 ]; then ok "$N commits, árbol limpio"
  else printf '  \033[33mAVISO\033[0m %s cambios sin commitear (no bloquea)\n' "$SUCIO"; ok "$N commits"; fi
else
  mal "el vault no está bajo control de versiones"
fi

printf '\n'
if [ "$FALLOS" -eq 0 ]; then
  printf '\033[32m\033[1mCERTIFICADO: el sistema cumple todos los invariantes.\033[0m\n'
  printf 'Alcance: forma, estructura, coherencia interna, respaldo e historial.\n'
  printf '\033[33mNO certifica que el CONTENIDO sea cierto.\033[0m Eso exige la fuente primaria.\n'
  exit 0
else
  printf '\033[31m\033[1mNO CERTIFICADO: %s comprobaciones fallaron.\033[0m\n' "$FALLOS"
  exit 1
fi
