import json

from scripts import migrar


def test_ensaio_vira_leva(tmp_path):
    ensaio = tmp_path / "2026-10-07-primeira-leva.py"
    ensaio.write_text(
        'ROTEIROS = [{"chave": "r1", "tema": "T", "gancho": "G", "corpo": "C",'
        ' "fechamento": "F", "gravacao": "Lo-fi", "formato": "x", "alavanca": "y"}]\n',
        encoding="utf-8")
    dado = migrar.leva_do_ensaio(ensaio, "Pedro Roim", "pedro")
    assert dado["data"] == "2026-10-07"
    assert dado["roteiros"][0]["gravacao"] == "Lo-fi"
    assert "alavanca" not in dado["roteiros"][0]


def test_ensaio_sem_roteiros_devolve_none(tmp_path):
    ensaio = tmp_path / "2026-10-02-solto.py"
    ensaio.write_text("X = 1\n", encoding="utf-8")
    assert migrar.leva_do_ensaio(ensaio, "P", "p") is None


def test_copiar_cliente(tmp_path):
    origem = tmp_path / "ar" / "esteira2" / "clientes" / "dani"
    (origem / "coleta" / "mp4").mkdir(parents=True)
    (origem / "coleta" / "2026-09-29").mkdir()
    (origem / "retrato.json").write_text(json.dumps({"nome": "Dani", "slug": "dani"}))
    (origem / "coleta" / "transcricoes.md").write_text("fala")
    (origem / "coleta" / "mp4" / "a.mp4").write_text("video")
    (origem / "coleta" / "2026-09-29" / "estudo.md").write_text("estudo")
    destino = tmp_path / "sr" / "clientes" / "dani"
    migrar.copiar_cliente(origem, destino)
    assert (destino / "retrato.json").exists()
    assert (destino / "transcricoes.md").read_text() == "fala"
    assert (destino / "extras" / "2026-09-29" / "estudo.md").exists()
    assert not list(destino.rglob("*.mp4"))
