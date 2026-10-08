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


def test_familia_e_versao():
    assert migrar.familia_e_versao("2026-09-18-dez-v2") == ("dez", 2)
    assert migrar.familia_e_versao("2026-09-17-dez-a-mao") == ("dez", 1)
    assert migrar.familia_e_versao("2026-09-21-cinco-de-teste") == ("cinco", 1)
    assert migrar.familia_e_versao("2026-10-05-semana-05-10") == ("semana-05-10", 1)
    assert migrar.familia_e_versao("2026-10-05-semana-05-10-v4") == ("semana-05-10", 4)
    assert migrar.familia_e_versao("2026-09-28-semana-28-09") == ("semana-28-09", 1)


def test_separar_versoes_deixa_so_a_ultima():
    nomes = ["2026-09-17-dez-a-mao", "2026-09-18-dez-v2", "2026-09-21-dez-v6",
             "2026-09-21-leva-v5", "2026-09-24-cinco-v1", "2026-09-24-cinco-v3",
             "2026-09-24-cinco-v2", "2026-09-30-lancamento-so-os-dois"]
    ficam, rascunhos = migrar.separar_versoes(nomes)
    assert sorted(ficam) == ["2026-09-21-dez-v6", "2026-09-21-leva-v5",
                             "2026-09-24-cinco-v3", "2026-09-30-lancamento-so-os-dois"]
    assert sorted(rascunhos) == ["2026-09-17-dez-a-mao", "2026-09-18-dez-v2",
                                 "2026-09-24-cinco-v1", "2026-09-24-cinco-v2"]


def test_felipe_transcricoes_so_dos_videos_dele(tmp_path):
    leg = tmp_path / "leg"
    leg.mkdir()
    (leg / "felipe-pare-de-correr-atras-do-dinheiro.txt").write_text("texto um")
    (leg / "felipe-quero-construir-algo-que-faca-sentido.txt").write_text("texto dois")
    (leg / "alfredo-posicionamento-socio-g4.txt").write_text("alfredo")
    alvo = tmp_path / "transcricoes.md"
    migrar.transcricoes_do_felipe(leg, alvo)
    texto = alvo.read_text()
    assert "texto um" in texto and "texto dois" in texto and "alfredo" not in texto
