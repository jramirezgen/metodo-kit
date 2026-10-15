"""Cada regla de dag_lib se prueba sembrando su defecto: una regla que nunca se vio fallar no se sabe si funciona."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dag_lib  # noqa: E402

LIMPIO = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}   # un hook que corre tests hereda GIT_DIR


def git(raiz, *a):
    return subprocess.run(["git", "-C", str(raiz), *a], capture_output=True, text=True, check=True, env=LIMPIO).stdout


def repo(tmp_path, nombre="r"):
    r = tmp_path / nombre
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    git(r, "config", "user.email", "t@t")
    git(r, "config", "user.name", "t")
    return r


def commit(r, ruta, texto="x"):
    p = r / ruta
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(texto)
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", ruta)
    return git(r, "rev-parse", "--short", "HEAD").strip()


def nodo(id, tipo="infra", dep=(), entrega="docs/x.md", cubre=(), estado="pendiente", **extra):
    return dict(id=id, fase="F0", tipo=tipo, titulo=id, depende_de=list(dep), entrega=entrega,
                hecho_cuando="algo", cubre=list(cubre), estado=estado, **extra)


CONF = dag_lib.Config(proyecto="P", hoja="REL-1.0.0")


def plan_minimo():
    return [nodo("A"), nodo("PRE", "preinscripcion", ["A"], "docs/pre/E1.md", ["E1"]),
            nodo("C", "corrida", ["PRE"], "scripts/c.py", ["E1"]),
            nodo("E1", "eureka", ["C"], "registro/veredictos.jsonl#E1", ["E1"]),
            nodo("R1", "revision", ["E1"], "docs/revisiones/R1.md"),
            nodo("REL-1.0.0", "release", ["E1", "R1"], "CHANGELOG.md")]


def test_plan_minimo_valido(tmp_path):
    assert dag_lib.validar(plan_minimo(), repo(tmp_path), CONF) == []


@pytest.mark.parametrize("nombre,siembra,esperado", [
    ("ciclo", lambda p: p[0]["depende_de"].append("C"), "ciclo"),
    ("dependencia inexistente", lambda p: p[0]["depende_de"].append("Z"), "no existe"),
    ("dos hojas", lambda p: p.append(nodo("X", dep=["A"])), "única hoja"),
    ("estado fuera del vocabulario", lambda p: p[0].update(estado="casi"), "vocabulario"),
    ("avanzar sobre lo abierto", lambda p: p[2].update(estado="en_curso"), "en_curso sobre"),
    ("hecho sin commit", lambda p: p[0].update(estado="hecho", evidencia="deadbee"), "sin un commit"),
    ("juzgado fuera de eureka", lambda p: p[0].update(estado="juzgado"), "juzgado"),
    ("eureka sin preinscripción", lambda p: p[1].update(cubre=[]), "preinscripciones"),
    ("corrida sin eureka", lambda p: p[2].update(cubre=[]), "no declara qué eureka"),
    ("release sin revisión", lambda p: p[5].update(depende_de=["E1"]), "revisión adversarial"),
    ("hecho_cuando largo", lambda p: p[0].update(hecho_cuando="x" * 801), "hecho_cuando"),
    ("nadie cubre lo requerido", None, "nadie cubre"),
])
def test_cada_regla_muerde(tmp_path, nombre, siembra, esperado):
    p, conf = plan_minimo(), CONF
    if siembra:
        siembra(p)
    else:
        conf = dag_lib.Config(proyecto="P", hoja="REL-1.0.0", requerido=["D-001"])
    fallos = dag_lib.validar(p, repo(tmp_path), conf)
    assert any(esperado in f for f in fallos), (nombre, fallos)


def test_hecho_con_evidencia_que_toca_su_entrega(tmp_path):
    r = repo(tmp_path)
    sha = commit(r, "docs/x.md")
    p = plan_minimo()
    p[0].update(estado="hecho", evidencia=sha)
    assert dag_lib.validar(p, r, CONF) == []
    otro = commit(r, "docs/otro.md")
    p[0].update(evidencia=otro)
    assert any("no toca ninguna ruta" in f for f in dag_lib.validar(p, r, CONF))


def test_la_revision_tiene_que_ser_fresca_en_cada_release(tmp_path):
    """Una revisión que ya sirvió a la release anterior no cuenta para la siguiente."""
    p = plan_minimo()
    p[-1]["id"] = "REL-0.1.0"
    p += [nodo("B", dep=["REL-0.1.0"]), nodo("REL-1.0.0", "release", ["B", "R1"], "CHANGELOG.md")]
    fallos = dag_lib.validar(p, repo(tmp_path), CONF)
    assert any("REL-1.0.0" in f and "revisión adversarial" in f for f in fallos), fallos
    p += [nodo("R2", "revision", ["B"], "docs/revisiones/R2.md")]
    p[-2]["depende_de"] = ["B", "R2"]
    assert dag_lib.validar(p, repo(tmp_path, "s"), CONF) == []


def test_externo_cierra_sólo_con_tag_y_nodo_cerrado_en_el_otro_repo(tmp_path):
    otro = repo(tmp_path, "otro")
    commit(otro, "registro/nodos.jsonl", json.dumps({"nodo": "F2.01", "estado": "en_curso", "fecha": "2026-10-05"}) + "\n")
    git(otro, "tag", "v0.5.0")
    yo = repo(tmp_path, "yo")
    conf = dag_lib.Config(proyecto="P", hoja="REL-1.0.0", externos={"OTRO": str(otro)})
    p = plan_minimo()
    p.insert(1, nodo("X.01", "externo", [], "OTRO@v0.5.0#F2.01", estado="hecho", evidencia="OTRO@v0.5.0"))
    p[2]["depende_de"] = ["A", "X.01"]
    assert any("F2.01" in f and "no está cerrado" in f for f in dag_lib.validar(p, yo, conf))
    with open(otro / "registro/nodos.jsonl", "a") as f:
        f.write(json.dumps({"nodo": "F2.01", "estado": "hecho", "evidencia": "abc", "fecha": "2026-10-06"}) + "\n")
    git(otro, "add", "-A"); git(otro, "commit", "-q", "-m", "cierra"); git(otro, "tag", "-f", "v0.5.0")
    assert dag_lib.validar(p, yo, conf) == []
    p[1]["evidencia"] = "OTRO@v9.9.9"
    assert any("tag" in f for f in dag_lib.validar(p, yo, conf))


def test_borrar_un_protegido_exige_declararlo(tmp_path):
    p = plan_minimo()
    nuevo = [x for x in p if x["id"] != "C"]
    nuevo[2]["depende_de"] = ["PRE"]
    assert any("desapareció" in f for f in dag_lib.comparar(p, nuevo, {}))
    assert dag_lib.comparar(p, nuevo, {"C": "motivo"}) == []


def test_listos_por_profundidad():
    p = plan_minimo()
    p[0]["estado"] = "hecho"
    assert [x["id"] for x in dag_lib.listos(p)] == ["PRE"]


def test_registro_append_only(tmp_path):
    r = repo(tmp_path)
    commit(r, "registro/nodos.jsonl", '{"nodo": "A", "estado": "hecho", "fecha": "2026-10-05"}\n')
    assert dag_lib.violaciones_append_only(r) == []
    (r / "registro/nodos.jsonl").write_text('{"nodo": "A", "estado": "pendiente", "fecha": "2026-10-05"}\n')
    assert any("cambia" in f for f in dag_lib.violaciones_append_only(r))


def _dos_ramas_que_anaden(tmp_path):
    """main y dev añaden cada una su línea al registro tras una base común; dev mergea main sin rebase."""
    A = '{"nodo": "A", "estado": "hecho", "fecha": "2026-10-05"}\n'
    M = '{"nodo": "M", "estado": "hecho", "fecha": "2026-10-06"}\n'
    D = '{"nodo": "D", "estado": "hecho", "fecha": "2026-10-07"}\n'
    r = repo(tmp_path)
    commit(r, "registro/nodos.jsonl", A)
    git(r, "checkout", "-q", "-b", "dev")
    commit(r, "registro/nodos.jsonl", A + D)
    git(r, "checkout", "-q", "main")
    commit(r, "registro/nodos.jsonl", A + M)
    git(r, "checkout", "-q", "dev")
    subprocess.run(["git", "-C", str(r), "merge", "-q", "--no-ff", "main"], capture_output=True, env=LIMPIO)
    return r, A, M, D


def _cierra_merge(r, texto):
    (r / "registro/nodos.jsonl").write_text(texto)
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "merge")


def test_registro_append_only_tras_merge_de_dos_ramas(tmp_path):
    """Un merge que conserva las líneas de los dos padres (las del primero delante, intactas) no viola el append-only, aunque
    el orden por fecha de `git log` entrelace las dos ramas."""
    r, A, M, D = _dos_ramas_que_anaden(tmp_path)
    _cierra_merge(r, A + D + M)
    assert dag_lib.violaciones_append_only(r) == []


def test_merge_que_pierde_una_linea_del_segundo_padre_viola(tmp_path):
    r, A, M, D = _dos_ramas_que_anaden(tmp_path)
    _cierra_merge(r, A + D)
    assert any("segundo padre" in f for f in dag_lib.violaciones_append_only(r))


def test_merge_que_reordena_el_primer_padre_viola(tmp_path):
    r, A, M, D = _dos_ramas_que_anaden(tmp_path)
    _cierra_merge(r, A + M + D)
    assert any("cambia" in f for f in dag_lib.violaciones_append_only(r))


def test_estado_de_nodos_manda_la_ultima_linea(tmp_path):
    r = repo(tmp_path)
    (r / "registro").mkdir()
    (r / "registro/nodos.jsonl").write_text(
        '{"nodo": "A", "estado": "en_curso", "fecha": "2026-10-05"}\n'
        '{"nodo": "A", "estado": "hecho", "evidencia": "abc", "fecha": "2026-10-06"}\n')
    assert dag_lib.estado_de_nodos(r)["A"][0] == "hecho"
    assert dag_lib.validar_registro(r, CONF) == []


def test_config_desde_json(tmp_path):
    (tmp_path / "dag.json").write_text(json.dumps({"proyecto": "Q", "hoja": "REL-2.0.0", "hecho_max": 500}))
    c = dag_lib.Config.leer(tmp_path / "dag.json")
    assert (c.proyecto, c.hoja, c.hecho_max) == ("Q", "REL-2.0.0", 500)
    (tmp_path / "dag.json").write_text(json.dumps({"proyecto": "Q", "hoja": "R", "clave_rara": 1}))
    with pytest.raises(ValueError, match="clave_rara"):
        dag_lib.Config.leer(tmp_path / "dag.json")


def test_instalar_y_cli_de_punta_a_punta(tmp_path):
    """La bala trazadora: instalar en un repo vacío, escribir un plan, validar, regenerar ESTADO y comprobarlo."""
    r = repo(tmp_path)
    aqui = Path(__file__).resolve().parents[1]
    corre = lambda *a: subprocess.run([sys.executable, *map(str, a)], capture_output=True, text=True, env=LIMPIO)
    assert corre(aqui / "instalar.py", r, "--proyecto", "P", "--hoja", "REL-1.0.0", "--aplicar").returncode == 0
    (r / "plan/plan.json").write_text(json.dumps({"proyecto": "P", "version_plan": 1, "fecha": "2026-10-05",
                                                  "nodos": plan_minimo(), "degradaciones": {}}))
    assert corre(r / "plan/dag.py", "validar").returncode == 0
    assert corre(r / "plan/dag.py", "estado").returncode == 0
    assert corre(r / "plan/dag.py", "estado", "--comprobar").returncode == 0
    assert "**A**" in corre(r / "plan/dag.py", "siguiente").stdout or "A " in corre(r / "plan/dag.py", "siguiente").stdout
    with open(r / "registro/nodos.jsonl", "a") as f:     # el estado sale del registro: hecho sin commit muerde
        f.write(json.dumps({"nodo": "A", "estado": "hecho", "evidencia": "deadbee", "fecha": "2026-10-05"}) + "\n")
    assert "sin un commit" in corre(r / "plan/dag.py", "validar").stderr


def _bitacora_reescrita(tmp_path):
    """Dos bitácoras; la de 10-03 reescribe en el último commit una línea ya escrita."""
    r = repo(tmp_path)
    commit(r, "docs/bitacora/2026-10-03.md", "a\n")
    commit(r, "docs/bitacora/2026-10-04.md", "b\n")
    commit(r, "docs/bitacora/2026-10-03.md", "A\n")
    return r, git(r, "rev-parse", "HEAD").strip()[:7]


def test_rectificada_exime_solo_esa_ruta_en_ese_commit(tmp_path):
    """Una reescritura no declarada falla; declarada vale sólo para esa ruta@sha: ni otro commit ni otro fichero."""
    r, sha = _bitacora_reescrita(tmp_path)
    av = lambda conf: dag_lib.violaciones_append_only(r, "docs/bitacora", ".md", conf.exentas())
    conf = lambda rect: dag_lib.Config(proyecto="P", hoja="R", rectificadas=rect)
    assert any("2026-10-03.md" in f for f in av(conf({})))
    assert av(conf({f"docs/bitacora/2026-10-03.md@{sha}": "errata de fecha, declarada"})) == []
    assert av(conf({"docs/bitacora/2026-10-03.md@0000000": "otro commit"}))                 # otro commit: sigue fallando
    assert av(conf({f"docs/bitacora/2026-10-04.md@{sha}": "otro fichero"}))                 # otra ruta: sigue fallando
    commit(r, "docs/bitacora/2026-10-03.md", "B\n")                                         # segunda reescritura
    assert any("2026-10-03.md" in f for f in av(conf({f"docs/bitacora/2026-10-03.md@{sha}": "sólo la primera"})))


def test_rectificada_exige_motivo_y_forma(tmp_path):
    for malo in ({"docs/bitacora/x.md@abcdef1": ""}, {"docs/bitacora/x.md@abcdef1": "  "},
                 {"docs/bitacora/x.md": "sin sha"}, {"docs/bitacora/x.md@abc": "sha corto"}):
        (tmp_path / "dag.json").write_text(json.dumps({"proyecto": "Q", "hoja": "R", "rectificadas": malo}))
        with pytest.raises(ValueError, match="rectificada .*(motivo|ruta@sha7)"):
            dag_lib.Config.leer(tmp_path / "dag.json")


def test_validar_lista_las_rectificaciones_declaradas(tmp_path):
    """Una exención no queda silenciosa: `dag.py validar` la imprime con su motivo."""
    r = repo(tmp_path)
    aqui = Path(__file__).resolve().parents[1]
    corre = lambda *a: subprocess.run([sys.executable, *map(str, a)], capture_output=True, text=True, env=LIMPIO)
    assert corre(aqui / "instalar.py", r, "--proyecto", "P", "--hoja", "REL-1.0.0", "--aplicar").returncode == 0
    (r / "plan/plan.json").write_text(json.dumps({"proyecto": "P", "version_plan": 1, "fecha": "2026-10-05",
                                                  "nodos": plan_minimo(), "degradaciones": {}}))
    commit(r, "docs/bitacora/2026-10-03.md", "a\n")
    commit(r, "docs/bitacora/2026-10-03.md", "A\n")
    sha = git(r, "rev-parse", "HEAD").strip()[:7]
    assert corre(r / "plan/dag.py", "validar").returncode == 1
    conf = json.loads((r / "plan/dag.json").read_text())
    conf["rectificadas"] = {f"docs/bitacora/2026-10-03.md@{sha}": "errata declarada"}
    (r / "plan/dag.json").write_text(json.dumps(conf))
    salida = corre(r / "plan/dag.py", "validar")
    assert salida.returncode == 0, salida.stderr
    assert f"docs/bitacora/2026-10-03.md@{sha}" in salida.stdout and "errata declarada" in salida.stdout


# ── git falla cerrado (INC-044 de AQUERONTE): un git que no responde nunca da la comprobación por buena ──
def test_append_only_sin_repo_git_falla_cerrado(tmp_path):
    """Un registro fuera de un repo git (o con el repo roto) no tiene historia que comprobar: es un error, no un verde."""
    (tmp_path / "registro").mkdir()
    (tmp_path / "registro/nodos.jsonl").write_text('{"nodo": "A", "estado": "hecho", "fecha": "2026-10-05"}\n')
    with pytest.raises(dag_lib.GitRoto):
        dag_lib.violaciones_append_only(tmp_path)
    with pytest.raises(dag_lib.GitRoto):
        dag_lib.versiones_del_plan(tmp_path)


def test_append_only_con_un_objeto_que_falta_falla_cerrado(tmp_path):
    """Si una versión commiteada del registro no se puede leer (objeto perdido, sha que no existe), no se salta."""
    r = repo(tmp_path)
    commit(r, "registro/nodos.jsonl", "a\n")
    blob = git(r, "rev-parse", "HEAD:registro/nodos.jsonl").strip()
    commit(r, "registro/nodos.jsonl", "a\nb\n")
    assert dag_lib.violaciones_append_only(r) == []
    (r / ".git/objects" / blob[:2] / blob[2:]).unlink()
    with pytest.raises(dag_lib.GitRoto):
        dag_lib.violaciones_append_only(r)


def test_un_repo_sin_commits_no_es_un_repo_roto(tmp_path):
    r = repo(tmp_path)
    (r / "registro").mkdir()
    (r / "registro/nodos.jsonl").write_text("a\n")
    assert dag_lib.violaciones_append_only(r) == []
    assert dag_lib.versiones_del_plan(r) == []


def test_validar_sin_repo_git_sale_con_error(tmp_path):
    """La CLI no imprime «en verde» si git no responde."""
    aqui = Path(__file__).resolve().parents[1]
    r = repo(tmp_path)
    corre = lambda *a: subprocess.run([sys.executable, *map(str, a)], capture_output=True, text=True, env=LIMPIO)
    assert corre(aqui / "instalar.py", r, "--proyecto", "P", "--hoja", "REL-1.0.0", "--aplicar").returncode == 0
    (r / "plan/plan.json").write_text(json.dumps({"proyecto": "P", "version_plan": 1, "fecha": "2026-10-05",
                                                  "nodos": plan_minimo(), "degradaciones": {}}))
    assert corre(r / "plan/dag.py", "validar").returncode == 0
    import shutil
    shutil.rmtree(r / ".git")
    salida = corre(r / "plan/dag.py", "validar")
    assert salida.returncode != 0 and "en verde" not in salida.stdout
