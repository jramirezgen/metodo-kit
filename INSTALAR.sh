#!/usr/bin/env bash
# Instala el kit: copia las skills a un directorio y reescribe las rutas del equipo original.
# Uso:  ./INSTALAR.sh [--skills DIR] [--vault DIR] [--cred DIR] [--agente claude|otro] [--sin-deps] [--ensayo]
#   --skills  dónde viven las skills            (defecto: ~/.claude/skills para claude, ~/metodo-skills para otro)
#   --vault   carpeta del segundo cerebro       (defecto: ~/segundo-cerebro; se crea si no existe)
#   --cred    carpeta de credenciales (fuera de cualquier repo)  (defecto: ~/.credenciales, modo 700)
#   --ensayo  sólo dice lo que haría
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
AGENTE=claude; SKILLS=""; VAULT="$HOME/segundo-cerebro"; CRED="$HOME/.credenciales"; DEPS=1; ENSAYO=0
while [ $# -gt 0 ]; do case "$1" in
  --skills) SKILLS="$2"; shift 2;; --vault) VAULT="$2"; shift 2;; --cred) CRED="$2"; shift 2;;
  --agente) AGENTE="$2"; shift 2;; --sin-deps) DEPS=0; shift;; --ensayo) ENSAYO=1; shift;;
  *) echo "argumento desconocido: $1" >&2; exit 2;; esac; done
if [ -z "$SKILLS" ]; then [ "$AGENTE" = claude ] && SKILLS="$HOME/.claude/skills" || SKILLS="$HOME/metodo-skills"; fi
run() { if [ "$ENSAYO" = 1 ]; then echo "[ensayo] $*"; else "$@"; fi; }

echo "== 1. dependencias"
falta=()
for c in git python3 rsync; do command -v "$c" >/dev/null || falta+=("$c"); done
if [ ${#falta[@]} -gt 0 ]; then echo "FALTAN: ${falta[*]}  (apt install ${falta[*]})"; [ "$DEPS" = 1 ] && exit 1; fi
python3 -c 'import sys; assert sys.version_info>=(3,10), "se necesita Python >= 3.10"'
if ! command -v uv >/dev/null; then
  echo "uv no está instalado (recomendado para entornos desechables):  curl -LsSf https://astral.sh/uv/install.sh | sh"; fi
command -v gh >/dev/null || echo "gh (GitHub CLI) no está: sólo hace falta para releases/PR (https://cli.github.com)"
command -v pandoc >/dev/null || echo "pandoc/xelatex no están: sólo hacen falta para construir papers en PDF"

echo "== 2. skills -> $SKILLS"
run mkdir -p "$SKILLS"
for d in "$AQUI"/skills/*/; do
  n="$(basename "$d")"
  if [ -e "$SKILLS/$n" ] && [ "$ENSAYO" = 0 ]; then echo "  ya existe $n (se respalda como $n.bak)"; rm -rf "$SKILLS/$n.bak"; mv "$SKILLS/$n" "$SKILLS/$n.bak"; fi
  run rsync -a "$d" "$SKILLS/$n/"
done

echo "== 3. reescritura de rutas (/mnt/f/... -> las tuyas)"
if [ "$ENSAYO" = 0 ]; then
  mkdir -p "$VAULT"/{wiki,raw/bandeja,alejandria} "$CRED"; chmod 700 "$CRED"
  for n in $(ls "$AQUI/skills"); do
    { grep -rIl -e '/mnt/f/' "$SKILLS/$n" 2>/dev/null || true; } | while read -r f; do
      sed -i -e "s#/mnt/f/skills/_personales#$SKILLS#g" -e "s#/mnt/f/OBSIDIAN#$VAULT#g" \
             -e "s#/mnt/f/src/api/api#$CRED#g" -e "s#/mnt/f/skills#$SKILLS#g" "$f"
    done
  done
  [ -f "$AQUI/docs/PROTOCOLO_SEGUNDO_CEREBRO.md" ] && [ ! -f "$VAULT/CLAUDE.md" ] && cp "$AQUI/docs/PROTOCOLO_SEGUNDO_CEREBRO.md" "$VAULT/CLAUDE.md"
fi

echo "== 4. enlaces para agentes que no son Claude Code"
if [ "$AGENTE" != claude ]; then
  echo "  Este agente debe leer los SKILL.md bajo $SKILLS/<skill>/SKILL.md. Añade a su archivo de instrucciones:"
  echo "    'Antes de planear o tocar un repo lee docs/REGLAS.md y las skills de $SKILLS (ver USAGE.md).'"
fi
echo "== 5. verificación"
[ "$ENSAYO" = 0 ] && VAULT_DIR="$VAULT" SKILLS_DIR="$SKILLS" bash "$AQUI/VERIFICAR.sh"
echo "Listo. Siguiente paso: lee USAGE.md (flujo completo) y docs/REGLAS.md."
