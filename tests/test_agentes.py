import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parents[1]
AGENTES = RAIZ / ".claude" / "agents"


def test_os_dois_agentes_existem_e_cabem_em_150_linhas():
    for nome in ("setor-roteirista", "setor-conferente"):
        arquivo = AGENTES / f"{nome}.md"
        texto = arquivo.read_text(encoding="utf-8")
        assert texto.startswith("---\n"), f"{nome} sem frontmatter"
        assert f"name: {nome}" in texto
        assert len(texto.splitlines()) <= 150, f"{nome} passou de 150 linhas"


def test_conferente_nao_escreve_roteiro():
    texto = (AGENTES / "setor-conferente.md").read_text(encoding="utf-8")
    cabeca = texto.split("---")[1]
    assert "Edit" not in cabeca


def test_conferente_grava_a_conferencia():
    cabeca = (AGENTES / "setor-conferente.md").read_text(encoding="utf-8").split("---")[1]
    assert "Write" in cabeca


def test_roteirista_recebe_a_chave():
    texto = (AGENTES / "setor-roteirista.md").read_text(encoding="utf-8")
    assert "a chave" in texto


def test_comecar_e_claude_md_usam_o_python_do_venv():
    for arquivo in (RAIZ / ".claude" / "commands" / "comecar.md", RAIZ / "CLAUDE.md"):
        texto = arquivo.read_text(encoding="utf-8")
        assert ".venv/bin/python -m" in texto, arquivo
        assert "python3 -m" not in texto and "python3 -c" not in texto, arquivo


def test_scripts_ensinam_o_python_do_venv():
    solto = re.compile(r"(?<!\.venv/bin/)\bpython3? -[mc]\b")
    for arquivo in sorted((RAIZ / "scripts").glob("*.py")):
        texto = arquivo.read_text(encoding="utf-8")
        assert not solto.search(texto), f"{arquivo.name} ensina python sem o .venv"


def test_referencias_valem_para_qualquer_campo_que_pede():
    for nome in ("setor-roteirista", "setor-conferente"):
        texto = (AGENTES / f"{nome}.md").read_text(encoding="utf-8")
        assert "regras_de_roteiro" in texto and "qualquer campo" in texto, nome
