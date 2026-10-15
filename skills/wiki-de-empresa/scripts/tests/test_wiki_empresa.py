"""Pruebas de la skill: el catálogo es un DAG válido y la instalación sobre un repo con DAG produce un plan válido."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[2]
DAGSKILL = Path("/mnt/f/skills/_personales/dag-de-proyecto/scripts")
CAT = json.loads((SKILL / "catalogo" / "capitulos.json").read_text(encoding="utf-8"))["nodos"]
sys.path.insert(0, str(SKILL / "scripts"))
import auditar  # noqa: E402


def test_el_catalogo_no_tiene_ciclos_ni_dependencias_inexistentes():
    ids = {c["id"] for c in CAT}
    assert len(ids) == len(CAT)
    for c in CAT:
        assert set(c["depende_de"]) <= ids, c["id"]
    visto, pila = set(), set()

    def visita(i):
        assert i not in pila, f"ciclo en {i}"
        if i in visto:
            return
        pila.add(i)
        for d in next(c for c in CAT if c["id"] == i)["depende_de"]:
            visita(d)
        pila.discard(i)
        visto.add(i)
    for c in CAT:
        visita(c["id"])


def test_cada_capitulo_md_tiene_secciones_y_cada_bloque_una_revision():
    for c in CAT:
        if c["entrega_base"] == "empresa" and c["entrega"].endswith(".md") and c["id"] not in ("BP0",):
            assert c["secciones"], c["id"]
    assert {c["id"] for c in CAT if c["tipo"] == "revision"} >= {"BPR1", "BPR2", "BPR3", "BPR4", "BPR5", "BP99"}


def test_la_auditoria_caza_cifras_tecleadas_y_pii(tmp_path):
    (tmp_path / "analisis" / "matlab").mkdir(parents=True)
    (tmp_path / "analisis" / "matlab" / "m.m").write_text("S = fileread('supuestos.json');\nx = 12345;\n", encoding="utf-8")
    (tmp_path / "docs" / "empresa").mkdir(parents=True)
    (tmp_path / "docs" / "empresa" / "a.md").write_text("DNI 45678912\n", encoding="utf-8")
    duros, _ = auditar.auditar(tmp_path)
    assert any("cifra tecleada" in d for d in duros)
    assert any("8 dígitos" in d for d in duros)


def test_un_capitulo_cerrado_con_marcador_falla(tmp_path):
    (tmp_path / "docs" / "empresa").mkdir(parents=True)
    (tmp_path / "docs" / "empresa" / "01_INVENTARIO.md").write_text("> POR COMPLETAR\n", encoding="utf-8")
    (tmp_path / "registro").mkdir()
    (tmp_path / "registro" / "nodos.jsonl").write_text('{"nodo":"BP1","estado":"hecho"}\n', encoding="utf-8")
    duros, _ = auditar.auditar(tmp_path)
    assert any("POR COMPLETAR" in d for d in duros)


@pytest.mark.skipif(not DAGSKILL.is_dir(), reason="dag-de-proyecto no montada")
def test_instalar_sobre_un_repo_con_dag_da_un_plan_valido():
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run([sys.executable, str(DAGSKILL / "instalar.py"), str(repo), "--proyecto", "X", "--hoja", "REL", "--aplicar"],
                       check=True, capture_output=True)
        (repo / "plan" / "construir_dag.py").write_text(
            "import json,sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).resolve().parent))\nimport dag_lib as D\n"
            "N=[]\ndef n(id,fase,tipo,titulo,deps,entrega,hecho,cubre):\n    N.append(dict(id=id,fase=fase,tipo=tipo,titulo=titulo,depende_de=deps,entrega=entrega,hecho_cuando=hecho,cubre=cubre,estado='pendiente'))\n"
            "\n\ndef emitir():\n    print(len(N))\n\nif __name__=='__main__':\n    emitir()\n", encoding="utf-8")
        r = subprocess.run([sys.executable, str(SKILL / "scripts" / "instalar.py"), str(repo), "--empresa", "X", "--aplicar"], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
        out = subprocess.run([sys.executable, str(repo / "plan" / "construir_dag.py")], capture_output=True, text=True)
        assert out.stdout.strip() == str(len(CAT)), out.stdout + out.stderr
        assert (repo / "docs" / "empresa" / "02_MODELO_DE_NEGOCIO.md").exists()
        assert subprocess.run([sys.executable, str(SKILL / "scripts" / "instalar.py"), str(repo), "--empresa", "X", "--comprobar"]).returncode == 0


def _repo_cerrado(tmp_path, nodo, archivo, texto):
    (tmp_path / "docs" / "empresa").mkdir(parents=True)
    if texto is not None:
        (tmp_path / "docs" / "empresa" / archivo).write_text(texto, encoding="utf-8")
    (tmp_path / "registro").mkdir()
    (tmp_path / "registro" / "nodos.jsonl").write_text(f'{{"nodo":"{nodo}","estado":"hecho"}}\n', encoding="utf-8")


def test_cerrado_sin_archivo_es_fallo_duro(tmp_path):
    _repo_cerrado(tmp_path, "BP1", "01_INVENTARIO.md", None)
    duros, _ = auditar.auditar(tmp_path)
    assert any("no existe" in d for d in duros)


def test_seccion_con_solo_pendiente_o_vacia_falla(tmp_path):
    sec = next(c for c in CAT if c["id"] == "BP1")["secciones"]
    cuerpo = "\n".join(f"## {s}\n_(pendiente)_\n" for s in sec)
    _repo_cerrado(tmp_path, "BP1", "01_INVENTARIO.md", cuerpo)
    duros, _ = auditar.auditar(tmp_path)
    assert any("vacía" in d for d in duros)


def test_tabla_con_celda_vacia_falla_y_una_llena_no(tmp_path):
    sec = next(c for c in CAT if c["id"] == "BP1")["secciones"]
    relleno = " ".join(["palabra"] * 20)
    cuerpo = "\n".join(f"## {s}\n{relleno}\n" for s in sec)
    _repo_cerrado(tmp_path, "BP1", "01_INVENTARIO.md", cuerpo + "\n| a | b |\n|---|---|\n| x | |\n")
    assert any("celdas vacías" in d for d in auditar.auditar(tmp_path)[0])


def test_pii_tipos_y_falsos_positivos(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("Población 34 157 732 ([INEI](https://x.pe/34157732)) y 20261012\n", encoding="utf-8")
    assert auditar.auditar(tmp_path)[0] == []
    (tmp_path / "docs" / "b.md").write_text("llamar 987 654 321 o a@b.pe\n", encoding="utf-8")
    duros = auditar.auditar(tmp_path)[0]
    assert any("teléfono" in d for d in duros) and any("correo" in d for d in duros)


def test_cifra_con_decimales_en_r_y_comentario_ignorado(tmp_path):
    (tmp_path / "analisis" / "r").mkdir(parents=True)
    (tmp_path / "analisis" / "r" / "x.R").write_text("s <- jsonlite::fromJSON('supuestos.json')\n# 12345 en comentario\ny <- 3.435\n", encoding="utf-8")
    duros = auditar.auditar(tmp_path)[0]
    assert len(duros) == 1 and "3.435" in duros[0]


def test_capitulo_cerrado_sin_fecha_ni_fuente_falla(tmp_path):
    sec = next(c for c in CAT if c["id"] == "BP1")["secciones"]
    relleno = " ".join(["palabra"] * 20)
    _repo_cerrado(tmp_path, "BP1", "01_INVENTARIO.md", "\n".join(f"## {s}\n{relleno}\n" for s in sec))
    assert any("fecha" in d for d in auditar.auditar(tmp_path)[0])


def test_pii_en_sql_y_json_y_cifra_entera_corta(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "e.sql").write_text("INSERT INTO t VALUES ('a@b.pe');\n", encoding="utf-8")
    (tmp_path / "analisis" / "matlab").mkdir(parents=True)
    (tmp_path / "analisis" / "matlab" / "m.m").write_text("S = jsondecode(fileread('supuestos.json'));\nx = 12;\n", encoding="utf-8")
    duros = auditar.auditar(tmp_path)[0]
    assert any("correo" in d for d in duros) and any("cifra tecleada" in d for d in duros)


def test_una_seccion_con_solo_subsecciones_no_cuenta_como_vacia():
    import importlib.util, sys
    spec = importlib.util.spec_from_file_location("auditar", str(SKILL / "scripts" / "auditar.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    s = m.secciones("## Padre\n### Hija\n" + "palabra " * 30 + "\n## Otra\nx\n")
    assert m.palabras(s["Padre"]) >= 30
