#!/usr/bin/env bash
# Da de baja las fuentes de 210526 que ya tienen archivo CERTIFICADO.
# Por defecto NO borra: imprime lo que haría. Borrar exige --aplicar.
#
# uso: tools/retirar_certificados.sh [--aplicar]
#
# Antes de borrar nada comprueba, para cada destino:
#   1. que exista COMPLETE.txt (el marcador que escribe archivar_210526.sh);
#   2. que el DESTINO siga íntegro — se re-verifica su SHA-256 contra
#      MANIFEST_DEST, porque es la copia que se conserva y el disco puede
#      degradarse entre el archivado y la baja;
#   3. que la FUENTE no haya cambiado desde que se archivó — se re-verifica su
#      SHA-256 contra MANIFEST_SOURCE. Si alguien tocó la fuente después, el
#      archivo ya no la representa y la baja se cancela.
# Cualquier fallo cancela SOLO ese directorio; los demás siguen.
set -uo pipefail

aplicar=0
[[ ${1:-} == --aplicar ]] && aplicar=1

archive_root=${ARCHIVE_ROOT:-/mnt/f/REPOSITORIOS/archivos/210526}
workspace=${WORKSPACE:-$(realpath "$(dirname "$0")/..")}
total=0; listos=0; bloqueados=0

for dest in "$archive_root"/*/; do
  [[ -f $dest/COMPLETE.txt ]] || continue
  src=$(sed -n 's/^origen=//p' "$dest/COMPLETE.txt")
  name=$(basename "$dest")
  [[ -n $src && -d $src ]] || { printf '[YA RETIRADA] %s\n' "$name"; continue; }
  case "$src" in "$workspace"/*) ;; *) printf '[BLOQUEADO] %s: fuente fuera del workspace\n' "$name"; bloqueados=$((bloqueados+1)); continue;; esac

  total=$((total+1))
  printf '\n== %s\n   fuente: %s (%s M)\n' "$name" "$src" "$(du -sm "$src" | cut -f1)"

  # 2. integridad del destino
  if ! ( cd "$dest" && sha256sum --quiet -c MANIFEST_DEST.sha256 ) 2>/dev/null; then
    printf '   [BLOQUEADO] el DESTINO no supera su propio SHA-256 — no se borra nada\n'
    bloqueados=$((bloqueados+1)); continue
  fi
  printf '   destino integro (%s ficheros)\n' "$(wc -l < "$dest/MANIFEST_DEST.sha256")"

  # 3. la fuente no ha cambiado: mismas rutas y mismo contenido
  if ! ( cd "$src" && sha256sum --quiet -c "$dest/MANIFEST_SOURCE.sha256" ) 2>/dev/null; then
    printf '   [BLOQUEADO] la FUENTE no supera su SHA-256 archivado — no se borra nada\n'
    bloqueados=$((bloqueados+1)); continue
  fi
  printf '   fuente integra (%s ficheros)\n' "$(wc -l < "$dest/MANIFEST_SOURCE.sha256")"

  if [[ $aplicar -eq 1 ]]; then
    rm -rf "$src" && printf '   BORRADA\n' || { printf '   [FALLO] al borrar\n'; bloqueados=$((bloqueados+1)); continue; }
  else
    printf '   LISTA PARA BORRAR (en seco; usa --aplicar)\n'
  fi
  listos=$((listos+1))
done

printf '\n=== %s candidatas · %s listas/borradas · %s bloqueadas\n' "$total" "$listos" "$bloqueados"
[[ $aplicar -eq 0 ]] && printf 'Modo SECO: no se ha borrado nada.\n'
[[ $bloqueados -eq 0 ]] || exit 1
exit 0
