"""Puxa os reels em que o cliente fala, pela Apify, na maquina dela.

Roda no Mac e nao na nuvem: a nuvem nao alcanca o Instagram, e o mp4 precisa de
disco para o Whisper ler. O token fica em `~/.config/setor-de-roteiros/apify.env`,
fora do repositorio, e nunca entra em prompt nem em commit.

Se a coleta trouxer menos de 10 videos com fala, a esteira para e avisa. Plano B:
ela cola os links. Escrever sem a voz e' o que produziu as quatro levas
reprovadas, e um retrato sobre cinco videos e' quase escrever sem a voz.

Os nomes dos campos da resposta do ator estao em `CAMPOS`. Se a Apify renomear
algum, muda aqui e no reels.json de amostra do teste, e em nenhum outro lugar.

Nao confirmado contra a API: uma chamada real ao ator, no perfil da cliente,
para validar CAMPOS, ficou pendente porque o token colado num chat em
2026-09-17 precisa ser trocado no painel da Apify antes de qualquer chamada
nova. Ate essa troca e uma primeira chamada de confirmacao, os nomes em CAMPOS
valem o que a documentacao do ator promete, nao o que a resposta real devolve.
"""

import json
import pathlib
import re
import urllib.request
import sys

ATOR = "apify~instagram-reel-scraper"
URL_API = "https://api.apify.com/v2/acts/{ator}/run-sync-get-dataset-items?token={token}"
ENV = pathlib.Path("~/.config/setor-de-roteiros/apify.env").expanduser()
VIDEOS_MINIMOS = 10
QUANTOS = 30

# Quando o ator devolve o campo principal vazio, o numero esta no reserva.
# Medido em 2026-09-20, no perfil da Sandra: os 28 reels vieram com
# videoViewCount nulo e videoPlayCount preenchido, e a coleta gravou 28 reels
# com 0 view. Zero em todo mundo nao reprova nada e vira media de views zero no
# retrato, que e' um dos numeros que diz o que o cliente grava hoje.
CAMPOS_RESERVA = {
    "views": "videoPlayCount",
}

CAMPOS = {
    "tipo": "type",
    "codigo": "shortCode",
    "url": "url",
    "quando": "timestamp",
    "segundos": "videoDuration",
    "views": "videoViewCount",
    "mp4": "videoUrl",
    "legenda": "caption",
    "perfil": "ownerUsername",
    "fixado": "isPinned",
}


def ler_token(caminho=None):
    """O token, do arquivo fora do repositorio."""
    arquivo = pathlib.Path(caminho or ENV)
    if arquivo.exists():
        for linha in arquivo.read_text(encoding="utf-8").splitlines():
            # O `strip` na linha existe porque arquivo de env editado a mao vem
            # com indentacao, e a mensagem de "sem token" descreveria o defeito
            # errado: a chave esta la, mal formatada.
            if linha.strip().startswith("APIFY_TOKEN="):
                token = linha.strip().split("=", 1)[1].strip()
                if not token:
                    raise ValueError(
                        "APIFY_TOKEN sem valor no apify.env: a chave esta la e o token nao. "
                        "Sem isso a Apify devolve 401, e o 401 nao explica isso")
                return token
    raise ValueError(
        "sem APIFY_TOKEN: grave a linha APIFY_TOKEN=<token> no apify.env da pasta "
        "de config do setor-de-roteiros, na casa do operador, e nunca no repositorio")


def entrada(perfil, quantos=QUANTOS):
    return {"username": [perfil.lstrip("@")], "resultsLimit": quantos}


def chamar(perfil, token, quantos=QUANTOS, abrir=None):
    """Uma chamada sincrona ao ator, que ja devolve os itens do dataset."""
    abrir = abrir or urllib.request.urlopen
    pedido = urllib.request.Request(
        URL_API.format(ator=ATOR, token=token),
        data=json.dumps(entrada(perfil, quantos)).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with abrir(pedido) as resposta:
        return json.loads(resposta.read().decode("utf-8"))


def _com_reserva(item, nome):
    """O valor do campo, ou o do campo reserva quando o principal vem vazio."""
    valor = item.get(CAMPOS[nome])
    if valor in (None, "") and nome in CAMPOS_RESERVA:
        return item.get(CAMPOS_RESERVA[nome])
    return valor


def normalizar(item, posicao=None):
    """Um item da resposta do ator vira o registro que a esteira usa.

    Confere antes de formatar, e o erro diz qual reel esta torto. Um
    `KeyError: 'url'` numa resposta de trinta itens obriga a olhar os trinta, e
    reel deletado ou em processamento sem `videoUrl` e' resposta comum de
    scraper.

    O `quando` e' conferido porque a esteira ordena por ele: data em outro
    formato passaria calada e embaralharia a ordem, e a ordem e' o que diz o que
    o cliente grava hoje.
    """
    quem = (item.get(CAMPOS["codigo"]) or item.get(CAMPOS["url"])
            or (f"na posicao {posicao}" if posicao is not None else "sem identificacao"))
    for chave in ("url", "codigo", "quando", "mp4"):
        if not str(item.get(CAMPOS[chave]) or "").strip():
            raise ValueError(f"reel {quem} sem {CAMPOS[chave]}")
    quando = str(item[CAMPOS["quando"]])
    if not re.match(r"\d{4}-\d{2}-\d{2}", quando):
        raise ValueError(
            f"reel {quem} com {CAMPOS['quando']} fora do formato ano-mes-dia: {quando!r}")
    try:
        segundos = int(round(float(item.get(CAMPOS["segundos"]) or 0)))
        views = int(_com_reserva(item, "views") or 0)
    except (TypeError, ValueError):
        raise ValueError(
            f"reel {quem} com duracao ou views que nao sao numero: "
            f"{item.get(CAMPOS['segundos'])!r} e {item.get(CAMPOS['views'])!r}")
    return {
        "url": item[CAMPOS["url"]],
        "codigo": item[CAMPOS["codigo"]],
        "quando": quando[:10],
        "segundos": segundos,
        "views": views,
        "mp4": item[CAMPOS["mp4"]],
        "legenda": (item.get(CAMPOS["legenda"]) or "").strip(),
    }


def escolher(itens, perfil):
    """So' video, so' do proprio perfil, sem os fixados, do mais novo ao mais velho.

    Fixado sai porque e' post antigo pendurado no topo: post fixado costuma ser
    campanha velha e entraria no retrato como se fosse o que ela grava hoje.
    """
    alvo = perfil.lstrip("@").lower()
    escolhidos = []
    for posicao, item in enumerate(itens):
        if not isinstance(item, dict):
            raise ValueError(f"o item na posicao {posicao} nao e' um mapa: {item!r}")
        if str(item.get(CAMPOS["tipo"]) or "").lower() != "video":
            continue
        if item.get(CAMPOS["fixado"]):
            continue
        if str(item.get(CAMPOS["perfil"]) or "").lower() != alvo:
            continue
        escolhidos.append(normalizar(item, posicao))
    escolhidos.sort(key=lambda reel: reel["quando"], reverse=True)
    return escolhidos


def conferir(reels, minimo=VIDEOS_MINIMOS):
    if len(reels) < minimo:
        raise ValueError(
            f"a coleta trouxe {len(reels)} vídeos e o mínimo é {minimo}: pare e avise. "
            "Plano B: ela cola os links")
    return reels


def gravar(reels, destino):
    pasta = pathlib.Path(destino)
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / "reels.json"
    caminho.write_text(json.dumps(reels, ensure_ascii=False, indent=1) + "\n",
                       encoding="utf-8")
    return caminho


def baixar(reels, destino, abrir=None):
    """Um mp4 por reel, e nao baixa de novo o que ja esta no disco."""
    abrir = abrir or (lambda url: urllib.request.urlopen(url).read())
    pasta = pathlib.Path(destino)
    pasta.mkdir(parents=True, exist_ok=True)
    novos = []
    for reel in reels:
        arquivo = pasta / f"{reel['codigo']}.mp4"
        if arquivo.exists():
            continue
        try:
            arquivo.write_bytes(abrir(reel["mp4"]))
        except Exception as erro:                      # noqa: o motivo vem no texto
            # Vinte e poucos downloads numa rodada: sem o codigo do reel na
            # mensagem, quem opera nao sabe qual tentar de novo.
            raise RuntimeError(f"nao baixei o reel {reel['codigo']}: {erro}") from erro
        novos.append(arquivo)
    return novos


def main(argv):
    if len(argv) < 3:
        print("uso: <pasta do cliente ou perfil> <@perfil> [quantos]")
        return 1
    pasta, perfil = pathlib.Path(argv[1]), argv[2]
    quantos = int(argv[3]) if len(argv) > 3 else QUANTOS
    itens = chamar(perfil, ler_token(), quantos)
    reels = conferir(escolher(itens, perfil))
    gravar(reels, pasta)
    baixados = baixar(reels, pasta / "mp4")
    print(f"{len(reels)} reels de {perfil}, {len(baixados)} mp4 novos em {pasta / 'mp4'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
