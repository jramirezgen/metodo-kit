#!/usr/bin/env python3
"""Mantiene espejos `bare` de los repos de trabajo en el disco F:.

Por qué existe (medido 2026-08-01): los repos de trabajo viven en ext4 dentro de
WSL. Su único respaldo era GitHub, y `fenix` no tenía ni eso — 0 commits, 0
remotos, 9 archivos sueltos. Un fallo del disco de WSL se llevaba el historial.

Qué NO es: una segunda copia de trabajo. Un espejo `bare` no tiene árbol de
trabajo, así que **no se puede editar y por tanto no puede divergir**. Esa es
justamente la avería que este montaje evita, y que ya se pagó dos veces en este
entorno (la skill `run-element` duplicada, y `sapyria-platform` duplicado el
2026-08-01).

Cada copia de trabajo recibe un remoto llamado `local` apuntando a su espejo:

    git push local --all        # respaldar
    git push local --tags

Uso:
    python3 espejar.py                      # simulacro sobre el dir por defecto
    python3 espejar.py --aplicar
    python3 espejar.py --trabajo ~/otro --espejos /mnt/f/REPOSITORIOS/espejos --aplicar
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# ⚠️ 2026-08-31: el defecto apuntaba a `Documents/RESEARCH/shewanella/210526`,
# workspace ARCHIVADO en F:\REPOSITORIOS\archivos\210526. Correr sin `--trabajo`
# encontraba 0 repos y reventaba con `max() arg is an empty sequence`: el respaldo
# no respaldaba nada. La ubicación canónica del código es la de la tarjeta de
# arranque del vault. Ver [[Ubicacion Canonica de Codigo y Migracion de 210526]].
TRABAJO_POR_DEFECTO = Path.home() / "Documents/REPOSITORIOS"
ESPEJOS_POR_DEFECTO = Path("/mnt/f/REPOSITORIOS/espejos")


def git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )


def descubrir(trabajo: Path) -> list[Path]:
    """Repos git de primer nivel. Sin lista hardcodeada: si aparece uno nuevo,
    entra solo la próxima vez que se corra."""
    return sorted(
        p for p in trabajo.iterdir() if p.is_dir() and (p / ".git").is_dir()
    )


def n_refs(repo: Path) -> int:
    r = git("show-ref", cwd=repo)
    return len([l for l in r.stdout.splitlines() if l.strip()])


def refs_de(repo: Path, bare: bool = False) -> set[str]:
    """Conjunto 'sha nombre' de refs locales, para comparar copia y espejo."""
    r = git("for-each-ref", "--format=%(objectname) %(refname)",
            "refs/heads", "refs/tags", cwd=repo)
    return {l.strip() for l in r.stdout.splitlines() if l.strip()}


def espejar(repo: Path, destino: Path, aplicar: bool) -> dict:
    nombre = repo.name
    espejo = destino / f"{nombre}.git"
    info = {"nombre": nombre, "refs": n_refs(repo), "espejo": espejo,
            "accion": "", "ok": None, "sucio": len(
                [l for l in git("status", "--porcelain", cwd=repo).stdout.splitlines() if l.strip()])}

    if info["refs"] == 0:
        info["accion"] = "SALTADO — 0 refs (repo sin ningún commit)"
        return info

    if not aplicar:
        info["accion"] = "crear espejo" if not espejo.exists() else "actualizar espejo"
        return info

    destino.mkdir(parents=True, exist_ok=True)

    if espejo.exists():
        r = git("remote", "update", "--prune", cwd=espejo)
        info["accion"] = "actualizado"
    else:
        r = git("clone", "--mirror", str(repo), str(espejo))
        info["accion"] = "creado"
    if r.returncode != 0:
        info["ok"] = False
        info["accion"] += f" — ERROR: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else '?'}"
        return info

    # El remoto `local` en la copia de trabajo es lo que vuelve usable el espejo.
    actual = git("remote", "get-url", "local", cwd=repo).stdout.strip()
    if actual != str(espejo):
        sub = "set-url" if actual else "add"
        git("remote", sub, "local", str(espejo), cwd=repo)

    # Verificación: el espejo debe contener exactamente las refs de la copia.
    faltan = refs_de(repo) - refs_de(espejo)
    info["ok"] = not faltan
    if faltan:
        info["accion"] += f" — ⛔ faltan {len(faltan)} refs en el espejo"
    return info


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trabajo", type=Path, default=TRABAJO_POR_DEFECTO)
    ap.add_argument("--espejos", type=Path, default=ESPEJOS_POR_DEFECTO)
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    if not args.trabajo.is_dir():
        sys.exit(f"error: no existe {args.trabajo}")

    repos = descubrir(args.trabajo)
    print(f"# Espejos de repos — {len(repos)} encontrados en {args.trabajo}")
    print(f"# Destino: {args.espejos}\n")

    filas = [espejar(r, args.espejos, args.aplicar) for r in repos]

    ancho = max(len(f["nombre"]) for f in filas)
    problemas = 0
    for f in filas:
        marca = {True: "✓", False: "✗", None: " "}[f["ok"]]
        sucio = f"  ⚠️ {f['sucio']} sin commitear" if f["sucio"] else ""
        print(f"  {marca} {f['nombre']:<{ancho}}  {f['refs']:>3} refs  {f['accion']}{sucio}")
        if f["ok"] is False or f["refs"] == 0:
            problemas += 1

    if args.aplicar:
        total = sum(
            p.stat().st_size for p in args.espejos.rglob("*") if p.is_file()
        ) if args.espejos.exists() else 0
        print(f"\nTamaño total de los espejos: {total / 1e6:.0f} MB")
        print("\nPara respaldar desde una copia de trabajo:")
        print("  git push local --all && git push local --tags")
    else:
        print("\n(simulacro — usa --aplicar)")

    if problemas:
        print(f"\n⚠️ {problemas} repo(s) necesitan atención (0 refs o refs faltantes).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
