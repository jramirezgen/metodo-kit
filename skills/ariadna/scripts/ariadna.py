#!/usr/bin/env python3
"""ariadna — el hilo en el disco de una fase de proyecto largo.

Una fase deja siempre el mismo rastro en `docs/mediciones/<fase>_<fecha>/`:

    PREINSCRIPCION.md      qué se cambia y qué criterios lo juzgan, ANTES de tocar nada
    PREINSCRIPCION.sha256  su huella; se commitea sola, antes que el cambio
    *.log / *.json         la evidencia, un fichero por criterio
    RESULTADO.md           veredicto, lo que no salió a la primera, discrepancias, lo que NO dice

Subcomandos (stdlib pura; se corre desde la raíz del repo):

    ariadna.py fase <nombre>            crea la carpeta con la plantilla de preinscripción
    ariadna.py sellar <carpeta>         escribe PREINSCRIPCION.sha256 (se niega si hay huecos «⟨…⟩»)
    ariadna.py verificar <carpeta>      comprueba que la preinscripción no cambió desde el sello
    ariadna.py cerrar <carpeta>         verifica y crea RESULTADO.md desde la plantilla
    ariadna.py estado [raiz]            lista las fases: sellada / cerrada / huella rota

Sale con 0 si todo está bien, 1 si algo no cuadra (lo nombra) y 2 si el uso es incorrecto.
"""
import datetime as _dt
import hashlib
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PLANTILLAS = AQUI.parent / "plantillas"
MEDICIONES = Path("docs/mediciones")
HUECO = re.compile(r"⟨[^⟩]*⟩")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _plantilla(nombre: str, **campos) -> str:
    texto = (PLANTILLAS / nombre).read_text(encoding="utf-8")
    for k, v in campos.items():
        texto = texto.replace("{{" + k + "}}", v)
    return texto


def fase(nombre: str) -> int:
    slug = re.sub(r"[^a-z0-9]+", "_", nombre.lower()).strip("_")
    if not slug:
        print("el nombre de la fase no puede quedar vacío")
        return 2
    hoy = _dt.date.today().isoformat()
    d = MEDICIONES / f"{slug}_{hoy}"
    if d.exists():
        print(f"ya existe {d}: una fase no se re-crea encima de su propia evidencia")
        return 1
    d.mkdir(parents=True)
    (d / "PREINSCRIPCION.md").write_text(_plantilla("PREINSCRIPCION.md", FASE=nombre, FECHA=hoy),
                                         encoding="utf-8")
    print(f"creada {d}/PREINSCRIPCION.md — rellena los ⟨huecos⟩ y luego: ariadna.py sellar {d}")
    return 0


def sellar(carpeta: str) -> int:
    d = Path(carpeta)
    pre = d / "PREINSCRIPCION.md"
    if not pre.is_file():
        print(f"falta {pre}")
        return 1
    huecos = HUECO.findall(pre.read_text(encoding="utf-8"))
    if huecos:
        print(f"la preinscripción tiene {len(huecos)} hueco(s) sin rellenar, p. ej. {huecos[0]}")
        return 1
    huella = d / "PREINSCRIPCION.sha256"
    if huella.exists():
        print(f"{huella} ya existe: una preinscripción se sella una vez. Si cambió, es otra fase")
        return 1
    huella.write_text(f"{_sha(pre)}  {pre.as_posix()}\n", encoding="utf-8")
    print(f"sellada: {huella}. Commitéala SOLA, antes de tocar el código.")
    return 0


def _verifica(d: Path) -> str:
    """'ok', 'sin_sello' o 'rota'.

    Vale cualquier `*.sha256` de la carpeta que se llame «…preinscrip…» o que cubra un
    fichero con ese nombre, no sólo `PREINSCRIPCION.sha256`: los repos que ya preinscribían
    antes de esta skill usan otros nombres (`PREINSCRIPCION_LAZO.sha256`), y a veces la
    preinscripción es el propio script (`inc066.preinscripcion.v1.sha256` cubre `inc066.py`).
    Darlos por «sin sello» sería mentir sobre su historia. La ruta de cada línea se busca
    relativa a la carpeta, a la raíz del repo o por su nombre dentro de la carpeta.
    """
    raiz = d.resolve()
    while raiz != raiz.parent and not (raiz / ".git").exists():
        raiz = raiz.parent
    # Una serie versionada (`x.preinscripcion.v1.sha256`, `.v2`…) se juzga por su ÚLTIMA
    # versión: la v1 de una preinscripción enmendada no coincide por construcción.
    ultima = {}
    for h in d.glob("*.sha256"):
        m = re.match(r"(.*)\.v(\d+)\.sha256$", h.name)
        tallo, v = (m.group(1), int(m.group(2))) if m else (h.name, 0)
        if v >= ultima.get(tallo, (-1, None))[0]:
            ultima[tallo] = (v, h)
    vistas, rotas = 0, 0
    for h in sorted(h for _, h in ultima.values()):
        for linea in h.read_text(encoding="utf-8", errors="replace").splitlines():
            partes = linea.split(maxsplit=1)
            if len(partes) != 2 or ("preinscrip" not in partes[1].lower()
                                    and "preinscrip" not in h.name.lower()):
                continue
            nombre = partes[1].lstrip("*").strip()
            cand = [d / nombre, raiz / nombre, d / Path(nombre).name]
            f = next((c for c in cand if c.is_file()), None)
            vistas += 1
            rotas += f is None or _sha(f) != partes[0]
    if not vistas:
        return "sin_sello"
    return "rota" if rotas else "ok"


def _tiene_preinscripcion(d: Path) -> bool:
    return any("preinscrip" in p.name.lower() for p in d.iterdir())


def verificar(carpeta: str) -> int:
    v = _verifica(Path(carpeta))
    print({"ok": "preinscripción intacta",
           "sin_sello": "sin PREINSCRIPCION.sha256: la fase no está sellada",
           "rota": "la preinscripción CAMBIÓ desde el sello: declararlo en RESULTADO.md, nunca en silencio"}[v])
    return 0 if v == "ok" else 1


def cerrar(carpeta: str) -> int:
    d = Path(carpeta)
    if verificar(carpeta):
        return 1
    res = d / "RESULTADO.md"
    if res.exists():
        print(f"{res} ya existe; no se pisa")
        return 1
    pre = d / "PREINSCRIPCION.md"
    lineas = pre.read_text(encoding="utf-8").splitlines() if pre.is_file() else []
    titulo = next((l[2:].strip() for l in lineas if l.startswith("# ")), d.name)
    res.write_text(_plantilla("RESULTADO.md", TITULO=titulo, FECHA=_dt.date.today().isoformat()),
                   encoding="utf-8")
    print(f"creado {res} — cada fila del veredicto cita su fichero de evidencia")
    return 0


def estado(raiz: str = ".") -> int:
    base = Path(raiz) / MEDICIONES
    fases = sorted(p for p in base.glob("*") if p.is_dir() and _tiene_preinscripcion(p)) if base.is_dir() else []
    if not fases:
        print(f"ninguna fase con preinscripción en {base}")
        return 0
    rotas = 0
    for p in fases:
        v = _verifica(p)
        rotas += v == "rota"
        cerrada = "cerrada" if (p / "RESULTADO.md").is_file() else "abierta"
        print(f"{ {'ok': 'sellada', 'sin_sello': 'SIN SELLO', 'rota': 'HUELLA ROTA'}[v]:12} {cerrada:8} {p.name}")
    return 1 if rotas else 0


def main(argv) -> int:
    ordenes = {"fase": fase, "sellar": sellar, "verificar": verificar, "cerrar": cerrar, "estado": estado}
    if not argv or argv[0] not in ordenes or (argv[0] != "estado" and len(argv) != 2):
        print(__doc__)
        return 2
    return ordenes[argv[0]](*argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
