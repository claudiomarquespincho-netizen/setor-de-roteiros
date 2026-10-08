import sys
"""A transcricao: a lista de palavras do cliente entra, e o documento sai legivel."""

import pytest

from scripts import transcricao

REEL = {
    "url": "https://www.instagram.com/p/DdMEgGcyLrb/",
    "codigo": "DdMEgGcyLrb",
    "quando": "2026-09-12",
    "segundos": 133,
    "views": 92828,
    "mp4": "https://cdn.example/DdMEgGcyLrb.mp4",
    "legenda": "Ore pelo lugar que você trabalha.",
}


def test_prompt_inicial_leva_as_palavras_do_cliente():
    assert transcricao.prompt_inicial(["Cherie", "scrub", "jaleco"]) == (
        "Vocabulário: Cherie, scrub, jaleco.")


def test_comando_passa_o_prompt_inicial_e_o_portugues():
    partes = transcricao.comando("/tmp/a.mp4", "/tmp/saida", ["Cherie"])
    assert partes[:3] == [sys.executable, "-m", "whisper"]
    assert "--language" in partes and partes[partes.index("--language") + 1] == "pt"
    assert partes[partes.index("--initial_prompt") + 1] == "Vocabulário: Cherie."


def test_prompt_inicial_recusa_lista_vazia():
    with pytest.raises(ValueError, match="sem palavras do cliente"):
        transcricao.prompt_inicial([])


def test_cabecalho_diz_qual_reel_esta_torto():
    torto = {k: v for k, v in REEL.items() if k != "views"}
    with pytest.raises(ValueError, match="reel DdMEgGcyLrb sem views"):
        transcricao.cabecalho(torto)


def test_montar_confere_todos_antes_de_escrever_qualquer_linha():
    torto = {k: v for k, v in REEL.items() if k != "url"}
    with pytest.raises(ValueError, match="sem url"):
        transcricao.montar("@cicinavarro", [REEL, torto], {"DdMEgGcyLrb": "fala"})


def test_cabecalho_tem_data_duracao_views_e_link():
    assert transcricao.cabecalho(REEL) == (
        "## 2026-09-12 · 133 s · 92828 views\nhttps://www.instagram.com/p/DdMEgGcyLrb/")


# Fala de amostra com tamanho de fala: depois que `parece_fala` passou a exigir
# 12 palavras, frase de tres palavras nao serve mais de dado de teste de ordem.
FALA_NOVA = ("Ore pelo lugar em que você trabalha, porque prosperidade não deveria "
             "ser uma oração que termina na gente.")
FALA_VELHA = ("Vamos de bastidores da Cherie comigo, porque hoje é dia de mostrar "
              "como nasce uma coleção aqui dentro.")


def test_montar_junta_os_blocos_do_mais_novo_ao_mais_velho():
    velho = dict(REEL, codigo="velho", quando="2026-08-04")
    doc = transcricao.montar("@cicinavarro", [REEL, velho],
                             {"DdMEgGcyLrb": FALA_NOVA, "velho": FALA_VELHA})
    assert doc.splitlines()[0] == "# Transcrições @cicinavarro (2 reels, 2026-08-04 a 2026-09-12)"
    assert doc.index(FALA_NOVA) < doc.index(FALA_VELHA)


def test_montar_deixa_de_fora_video_sem_fala_e_conta_quantos():
    doc = transcricao.montar("@cicinavarro", [REEL], {"DdMEgGcyLrb": "   "})
    assert "Ore pelo lugar" not in doc
    assert "0 reels" in doc.splitlines()[0]
    assert "1 vídeo sem fala" in doc


def test_palavras_do_cliente_sai_das_legendas_sem_repetir():
    reels = [dict(REEL, legenda="Cherie e o scrub"), dict(REEL, legenda="scrub novo")]
    assert transcricao.palavras_das_legendas(reels, minimo=5) == ["Cherie", "scrub"]


def test_bordao_de_legenda_nao_conta_como_fala():
    """Medido na coleta da Sandra: 2 reels mudos sairam com bordao de YouTube."""
    assert not transcricao.parece_fala("Inscreva-se no canal e ative o sininho.")
    assert not transcricao.parece_fala("Inscreva-se no nosso canal.")


def test_frase_solta_e_vazio_nao_contam_como_fala():
    assert not transcricao.parece_fala("")
    assert not transcricao.parece_fala("   ")
    assert not transcricao.parece_fala(".")
    assert not transcricao.parece_fala("Você viu só o sã.")


def test_fala_de_verdade_conta():
    fala = ("Olha para vocês verem, dois pães integrais, 60% de gordura, como é "
            "importante a gente avaliar os rótulos, gente.")
    assert transcricao.parece_fala(fala)


def test_video_sem_fala_fica_de_fora_do_documento():
    reels = [
        {"codigo": "aaa", "quando": "2026-05-10", "segundos": 60, "views": 10,
         "url": "https://exemplo/aaa"},
        {"codigo": "bbb", "quando": "2026-05-09", "segundos": 40, "views": 10,
         "url": "https://exemplo/bbb"},
    ]
    textos = {"aaa": "Inscreva-se no canal e ative o sininho.",
              "bbb": ("Bem sabemos nós, mulheres 40 mais, que inflamar pra gente é "
                      "facinho, né? Então essa é mais uma da série de drinks.")}
    documento = transcricao.montar("@sandra_gelmini", reels, textos)
    assert "1 vídeo sem fala ficou de fora" in documento
    assert "Inscreva-se" not in documento
    assert "facinho" in documento


def test_main_sem_reels_json_nao_quebra(tmp_path, capsys):
    assert transcricao.main(["transcricao", str(tmp_path), "@x"]) == 1
    assert "reels.json" in capsys.readouterr().out


def test_main_nao_sobrescreve_transcricoes(tmp_path):
    (tmp_path / "reels.json").write_text("[]", encoding="utf-8")
    (tmp_path / "transcricoes.md").write_text("antigo", encoding="utf-8")
    assert transcricao.main(["transcricao", str(tmp_path), "@x"]) == 1
    assert (tmp_path / "transcricoes.md").read_text(encoding="utf-8") == "antigo"
    assert transcricao.main(["transcricao", str(tmp_path), "@x", "--sobrescrever"]) == 0
