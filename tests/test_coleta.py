"""A coleta: so' video, so' do perfil, sem fixado, e para se vier pouco."""

import json

import pytest

from scripts import coleta

ITEM = {
    "type": "Video",
    "shortCode": "DdMEgGcyLrb",
    "url": "https://www.instagram.com/p/DdMEgGcyLrb/",
    "timestamp": "2026-09-12T18:04:11.000Z",
    "videoDuration": 133.4,
    "videoViewCount": 92828,
    "videoUrl": "https://cdn.example/DdMEgGcyLrb.mp4",
    "caption": "Ore pelo lugar que você trabalha.",
    "ownerUsername": "cicinavarro",
    "isPinned": False,
}


def test_normalizar_deixa_o_que_a_esteira_usa():
    assert coleta.normalizar(ITEM) == {
        "url": "https://www.instagram.com/p/DdMEgGcyLrb/",
        "codigo": "DdMEgGcyLrb",
        "quando": "2026-09-12",
        "segundos": 133,
        "views": 92828,
        "mp4": "https://cdn.example/DdMEgGcyLrb.mp4",
        "legenda": "Ore pelo lugar que você trabalha.",
    }


def test_escolher_tira_foto_fixado_e_video_de_outro_perfil():
    itens = [
        ITEM,
        dict(ITEM, shortCode="foto", type="Image"),
        dict(ITEM, shortCode="fixado", isPinned=True),
        dict(ITEM, shortCode="doutro", ownerUsername="marido"),
    ]
    assert [r["codigo"] for r in coleta.escolher(itens, "@cicinavarro")] == ["DdMEgGcyLrb"]


def test_escolher_vem_do_mais_novo_para_o_mais_velho():
    velho = dict(ITEM, shortCode="velho", timestamp="2026-08-04T10:00:00.000Z")
    itens = [velho, ITEM]
    assert [r["codigo"] for r in coleta.escolher(itens, "cicinavarro")] == [
        "DdMEgGcyLrb", "velho"]


def test_normalizar_diz_qual_reel_esta_sem_campo():
    sem = {k: v for k, v in ITEM.items() if k != "videoUrl"}
    with pytest.raises(ValueError, match="reel DdMEgGcyLrb sem videoUrl"):
        coleta.normalizar(sem)


def test_normalizar_recusa_campo_nulo():
    with pytest.raises(ValueError, match="sem videoUrl"):
        coleta.normalizar(dict(ITEM, videoUrl=None))


def test_normalizar_recusa_data_em_outro_formato():
    with pytest.raises(ValueError, match="fora do formato ano-mes-dia"):
        coleta.normalizar(dict(ITEM, timestamp="12/09/2026"))


def test_normalizar_recusa_duracao_que_nao_e_numero():
    with pytest.raises(ValueError, match="nao sao numero"):
        coleta.normalizar(dict(ITEM, videoDuration="trinta segundos"))


def test_escolher_recusa_item_que_nao_e_mapa():
    with pytest.raises(ValueError, match="na posicao 0 nao e' um mapa"):
        coleta.escolher(["DdMEgGcyLrb"], "@cicinavarro")


def test_ler_token_tolera_espaco_e_recusa_valor_vazio(tmp_path):
    com_espaco = tmp_path / "com-espaco.env"
    com_espaco.write_text("   APIFY_TOKEN=abc123\n", encoding="utf-8")
    assert coleta.ler_token(com_espaco) == "abc123"
    vazio = tmp_path / "vazio.env"
    vazio.write_text("APIFY_TOKEN=\n", encoding="utf-8")
    with pytest.raises(ValueError, match="sem valor"):
        coleta.ler_token(vazio)


def test_baixar_diz_qual_reel_falhou(tmp_path):
    def explode(url):
        raise OSError("conexão caiu")
    with pytest.raises(RuntimeError, match="nao baixei o reel DdMEgGcyLrb"):
        coleta.baixar([coleta.normalizar(ITEM)], tmp_path, abrir=explode)


def test_conferir_para_com_menos_de_dez():
    with pytest.raises(ValueError, match="9 vídeos"):
        coleta.conferir([coleta.normalizar(ITEM)] * 9)


def test_conferir_passa_com_dez():
    assert len(coleta.conferir([coleta.normalizar(ITEM)] * 10)) == 10


def test_entrada_do_ator():
    assert coleta.entrada("@cicinavarro", 30) == {
        "username": ["cicinavarro"], "resultsLimit": 30}


def test_ler_token_pega_a_chave(tmp_path):
    env = tmp_path / "apify.env"
    env.write_text("# comentário\nAPIFY_TOKEN=abc123\n", encoding="utf-8")
    assert coleta.ler_token(env) == "abc123"


def test_ler_token_sem_arquivo_diz_onde_por(tmp_path):
    with pytest.raises(ValueError, match="APIFY_TOKEN"):
        coleta.ler_token(tmp_path / "nao-existe.env")


def test_baixar_grava_um_arquivo_por_reel(tmp_path):
    reels = [coleta.normalizar(ITEM)]
    baixados = coleta.baixar(reels, tmp_path, abrir=lambda url: b"mp4 falso")
    assert baixados == [tmp_path / "DdMEgGcyLrb.mp4"]
    assert (tmp_path / "DdMEgGcyLrb.mp4").read_bytes() == b"mp4 falso"


def test_baixar_pula_o_que_ja_esta_no_disco(tmp_path):
    (tmp_path / "DdMEgGcyLrb.mp4").write_bytes(b"velho")
    def nao_chame(url):
        raise AssertionError("baixou de novo o que já estava lá")
    coleta.baixar([coleta.normalizar(ITEM)], tmp_path, abrir=nao_chame)


def test_gravar_reels_escreve_json_legivel(tmp_path):
    caminho = coleta.gravar([coleta.normalizar(ITEM)], tmp_path)
    assert json.loads(caminho.read_text(encoding="utf-8"))[0]["codigo"] == "DdMEgGcyLrb"


def test_views_caem_no_campo_reserva_quando_o_principal_vem_vazio():
    """Medido no perfil da Sandra em 2026-09-20: videoViewCount nulo, play count cheio."""
    item = {
        "type": "Video", "shortCode": "DZbJ84vNy3j",
        "url": "https://www.instagram.com/p/DZbJ84vNy3j/",
        "timestamp": "2026-06-10T23:48:22.000Z", "videoDuration": 17.4,
        "videoViewCount": None, "videoPlayCount": 754,
        "videoUrl": "https://exemplo/video.mp4", "caption": "", "ownerUsername": "sandra_gelmini",
    }
    assert coleta.normalizar(item)["views"] == 754


def test_views_preferem_o_campo_principal_quando_ele_existe():
    item = {
        "type": "Video", "shortCode": "DZbJ84vNy3j",
        "url": "https://www.instagram.com/p/DZbJ84vNy3j/",
        "timestamp": "2026-06-10T23:48:22.000Z", "videoDuration": 17.4,
        "videoViewCount": 9000, "videoPlayCount": 754,
        "videoUrl": "https://exemplo/video.mp4", "caption": "", "ownerUsername": "sandra_gelmini",
    }
    assert coleta.normalizar(item)["views"] == 9000


def test_main_grava_na_pasta_que_recebe(tmp_path, monkeypatch):
    reels = [dict(ITEM, shortCode=f"C{i}", videoUrl=f"https://cdn.example/C{i}.mp4")
             for i in range(12)]
    monkeypatch.setattr(coleta, "ler_token", lambda caminho=None: "t")
    monkeypatch.setattr(coleta, "chamar", lambda perfil, token, quantos=None: reels)
    monkeypatch.setattr(coleta, "baixar", lambda reels, destino, abrir=None: [])
    assert coleta.main(["coleta", str(tmp_path), "@cicinavarro"]) == 0
    assert (tmp_path / "reels.json").exists()


def test_main_nao_sobrescreve_reels_json(tmp_path, monkeypatch):
    (tmp_path / "reels.json").write_text("[]", encoding="utf-8")
    monkeypatch.setattr(coleta, "chamar", lambda *a, **k: pytest.fail("nao devia coletar"))
    assert coleta.main(["coleta", str(tmp_path), "@cicinavarro"]) == 1
    assert (tmp_path / "reels.json").read_text(encoding="utf-8") == "[]"


def test_main_sobrescreve_com_flag(tmp_path, monkeypatch):
    (tmp_path / "reels.json").write_text("[]", encoding="utf-8")
    reels = [dict(ITEM, shortCode=f"C{i}") for i in range(12)]
    monkeypatch.setattr(coleta, "ler_token", lambda caminho=None: "t")
    monkeypatch.setattr(coleta, "chamar", lambda perfil, token, quantos=None: reels)
    monkeypatch.setattr(coleta, "baixar", lambda reels, destino, abrir=None: [])
    assert coleta.main(["coleta", str(tmp_path), "@cicinavarro", "--sobrescrever"]) == 0
    assert len(json.loads((tmp_path / "reels.json").read_text(encoding="utf-8"))) == 12
