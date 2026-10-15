#!/usr/bin/env bash
# Archivo reanudable de una fuente de 210526. No elimina nunca la fuente.
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "uso: $0 RUTA_FUENTE NOMBRE_DESTINO [FICHERO_EXCLUSIONES]" >&2
  echo "  Sin el 3er argumento: copia todo salvo .git/ (comportamiento original)." >&2
  echo "  Con él: aplica además esas exclusiones, p.ej. tools/excluir_regenerable.txt" >&2
  exit 64
fi

source_dir=$(realpath "$1")
# WORKSPACE/ARCHIVE_ROOT permiten archivar un arbol distinto — o el propio
# workspace, que por definicion no esta "dentro de si mismo". Mismos overrides
# que retirar_certificados.sh, para que los dos scripts se usen igual.
workspace=${WORKSPACE:-$(realpath "$(dirname "$0")/..")}
dest_name=$2
archive_root=${ARCHIVE_ROOT:-/mnt/f/REPOSITORIOS/archivos/210526}
dest_dir="$archive_root/$dest_name"

filters=(--exclude='.git/')
excludes_file=""
if [[ $# -eq 3 ]]; then
  excludes_file=$(realpath "$3")
  [[ -f $excludes_file ]] || { echo "no existe $excludes_file" >&2; exit 66; }
  filters+=(--exclude-from="$excludes_file")
fi

case "$source_dir" in
  "$workspace"/*) ;;
  *) echo "La fuente debe estar dentro de $workspace" >&2; exit 65 ;;
esac

mkdir -p "$dest_dir"
rsync -aHAX --partial --append-verify "${filters[@]}" "$source_dir/" "$dest_dir/"

manifest_source="$dest_dir/MANIFEST_SOURCE.sha256"
manifest_dest="$dest_dir/MANIFEST_DEST.sha256"
# El manifiesto de ORIGEN se construye con el MISMO motor de filtros que la copia
# (rsync en seco), no con `find`. Cuando ambos lados se filtran por separado,
# divergen: ya pasó una vez con .git, que la copia excluía y el manifiesto no.
if [[ -n $excludes_file ]]; then
  empty_dir=$(mktemp -d); trap 'rm -rf "$empty_dir"' EXIT
  (
    cd "$source_dir"
    rsync -an --out-format='%n' "${filters[@]}" ./ "$empty_dir/" \
      | sed '/\/$/d' \
      | while IFS= read -r p; do [[ -f $p && ! -L $p ]] && printf '%s\0' "./$p"; done \
      | LC_ALL=C sort -z | xargs -0 -r sha256sum
  ) >"$manifest_source"
else
  (
    cd "$source_dir"
    find . -type d -name .git -prune -o -type f -print0 | LC_ALL=C sort -z | xargs -0 -r sha256sum
  ) >"$manifest_source"
fi
(
  cd "$dest_dir"
  find . -type f ! -name 'MANIFEST_*.sha256' -print0 | LC_ALL=C sort -z | xargs -0 -r sha256sum
) >"$manifest_dest"

diff -u "$manifest_source" "$manifest_dest"
printf 'origen=%s\ndestino=%s\nverificado=%s\n' "$source_dir" "$dest_dir" "$(date -Iseconds)" >"$dest_dir/COMPLETE.txt"
echo "Archivo verificado: $dest_dir"
