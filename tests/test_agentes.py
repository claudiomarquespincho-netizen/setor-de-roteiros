import pathlib

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
