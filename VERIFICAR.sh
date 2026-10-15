#!/usr/bin/env bash
# Comprueba que lo instalado funciona: tests de las skills con tests propios y un repo de prueba desechable.
set -uo pipefail
SK="${SKILLS_DIR:-$HOME/.claude/skills}"; ok=0; mal=0
paso() { if "$@" >/dev/null 2>&1; then echo "  ✓ $*" | cut -c1-110; ok=$((ok+1)); else echo "  ✗ $*" | cut -c1-110; mal=$((mal+1)); fi; }
for s in dag-de-proyecto wiki-de-proyecto code-principles ariadna; do [ -f "$SK/$s/SKILL.md" ] && ok=$((ok+1)) || { echo "  ✗ falta $s"; mal=$((mal+1)); }; done
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
( cd "$T" && git init -q repo && cd repo && git config user.email t@t && git config user.name t && echo x > a && git add a && git commit -qm "init" ) 
paso python3 "$SK/dag-de-proyecto/scripts/instalar.py" "$T/repo" --proyecto PRUEBA --hoja REL-0.1.0
paso python3 "$SK/dag-de-proyecto/scripts/instalar.py" "$T/repo" --proyecto PRUEBA --hoja REL-0.1.0 --aplicar
[ -d "$SK/dag-de-proyecto/scripts/tests" ] && command -v pytest >/dev/null && paso python3 -m pytest -q "$SK/dag-de-proyecto/scripts/tests"
echo "verificación: $ok bien, $mal mal"; [ "$mal" = 0 ]
