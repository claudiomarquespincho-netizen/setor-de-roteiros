"""Varre uma leva atras de trecho copiado de referencia ou de reel ja publicado.

Existe por causa de 24/09: o r1 da leva de 10 da Cici saiu escrito em cima do
reel da Uana Amorim, e o r7 fechava com a chamada literal de um reel que ela
ja tinha postado. Frase dele: "nao posso apresentar para a Cici videos
copiados". A conferencia rodou avulsa naquele dia e pegou os dois; aqui ela
vira script.

Duas fontes, e as duas reprovam:

1. referencia: reels de outros criadores que ele mandou de modelo. Da
   referencia entra a estrutura, nunca a frase.
2. publicado: os reels do proprio cliente. Repetir a fala de um video que ele
   ja postou e' entregar o mesmo video de novo.

O que o cliente disse em forms, audio ou WhatsApp nao entra aqui: e' material
dele, e o roteiro deve sair dali.

Pega sequencia literal de N palavras (6 por padrao). Parafrase passa, e por
isso comparar tema a tema com o que ele ja publicou continua sendo a mao.

Serve a qualquer cliente: o slug sai do caminho da leva.

Uso: python3 -m scripts.varredura_copia <leva.json> [N]
"""

import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def referencias(pasta):
    """Os criadores de referencia valem para todos, mais os colados daquela pasta.

    O reel da Uana que fez esta varredura nascer mora em referencias/, e nao nos
    colados: sem essa pasta a varredura deixava passar o caso de origem.
    O reels.json entra porque a legenda tambem e' texto do criador.
    """
    base = RAIZ / 'referencias'
    coletados = sorted(base.glob('*/transcricoes.md')) + sorted(base.glob('*/reels.json'))
    return coletados + sorted((pathlib.Path(pasta) / 'referencias').glob('*.md'))


def publicados(pasta):
    return [pathlib.Path(pasta) / 'transcricoes.md']


def _palavras(t):
    return re.findall(r"[a-zà-ú0-9']+", t.lower())


def _gramas(palavras, n):
    return {' '.join(palavras[i:i + n]) for i in range(len(palavras) - n + 1)}


def trechos_copiados(texto, corpus, n=6):
    """Os trechos do texto que aparecem literalmente no corpus, ja emendados.

    Duas janelas vizinhas que batem viram um trecho so, para o relatorio mostrar
    "eu sabia exatamente quanto tinha ficado na mesa" inteiro, e nao em 3 pedacos.
    """
    alvo = _gramas(_palavras(corpus), n)
    w = _palavras(texto)
    bate = [' '.join(w[i:i + n]) in alvo for i in range(len(w) - n + 1)]
    trechos, i = [], 0
    while i < len(bate):
        if not bate[i]:
            i += 1
            continue
        j = i
        while j + 1 < len(bate) and bate[j + 1]:
            j += 1
        trechos.append(' '.join(w[i:j + n]))
        i = j + 1
    return trechos


def varrer(roteiros, fontes, n=6):
    """Lista de (roteiro, origem, trecho). Vazia quando a leva passa."""
    achados = []
    for origem, caminhos in fontes.items():
        corpus = ' '.join(p.read_text(encoding='utf-8') for p in caminhos if p.exists())
        if not corpus:
            continue
        for r in roteiros:
            texto = ' '.join([r['gancho'], r['corpo'], r['fechamento']])
            for t in trechos_copiados(texto, corpus, n):
                achados.append((r['chave'], origem, t))
    return achados


def main(argv):
    from scripts import leva
    if len(argv) not in (2, 3):
        print('uso: python3 -m scripts.varredura_copia <leva.json> [N]', file=sys.stderr)
        return 2
    try:
        caminho = pathlib.Path(argv[1])
        n = int(argv[2]) if len(argv) > 2 else 6
        dado = leva.ler(caminho)
        pasta = leva.pasta_da_leva(caminho)
    except (ValueError, OSError) as erro:
        print(f'erro: {erro}', file=sys.stderr)
        return 2
    fontes = {'referencia': referencias(pasta), 'publicado': publicados(pasta)}
    for ps in fontes.values():
        for p in ps:
            if not p.exists():
                print('aviso: fonte nao encontrada, ficou fora da varredura:', p)
    achados = varrer(dado['roteiros'], fontes, n)
    if not achados:
        print(f'passou ({pasta.name}, {len(dado["roteiros"])} roteiros): nenhuma sequencia de '
              f'{n} palavras igual a referencia ou a reel publicado')
        return 0
    print(f'reprovou ({pasta.name}): {len(achados)} trecho(s) com {n}+ palavras iguais')
    for chave, origem, trecho in achados:
        print(f'   {chave} · {origem}: "{trecho}"')
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
