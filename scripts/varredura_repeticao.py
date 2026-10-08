"""Varre uma leva atras do que se repete dentro dela, e do que e' construcao minha.

Existe por causa do retorno dele em 2026-09-20: "voce escreve muito parecido
sempre, mapeei os padroes e nunca mais repita vicios na mesma leva (apenas
vicios do cliente)". Vicio do cliente pode repetir. O meu, nao.

Tres conferencias:

1. n-grama de 4 palavras que aparece em 2 roteiros ou mais, ignorando o que a
   fala dela tambem tem. Se a frase existe nas transcricoes dela, e' dela.
2. as construcoes minhas ja identificadas, que nao podem voltar nunca.
3. fechamento repetido: os N fechos tem que ser N, e nao metade com nomes
   diferentes.

Serve a qualquer cliente: o slug sai do caminho da leva, e a fala que absolve
repeticao e' a daquele cliente.

Mora aqui em ensaios/ porque cita caminho de fora, o que a trava do esteira2
proibe la dentro.

Uso: .venv/bin/python -m scripts.varredura_repeticao <leva.json>
"""

import collections
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def fala_do_cliente(pasta):
    """Os arquivos com a fala real daquele cliente ou perfil, os que existirem.

    A legenda escrita pelo proprio cliente conta como fala dele: na Sandra ela e'
    a fonte principal, porque so' 3 dos 28 reels tem voz.
    """
    pasta = pathlib.Path(pasta)
    fontes = [pasta / "transcricoes.md", pasta / "reels.json"]
    fontes += sorted((pasta / "fala").glob("*.md"))
    achados = [p for p in fontes if p.exists()]
    if not achados:
        raise FileNotFoundError(
            f'nenhuma fala em {pasta} para absolver repeticao: sem isso a varredura '
            'acusaria como minha toda muleta que e dele')
    return achados


# Construcao minha, apontada por ele. Nao volta, nem uma vez.
MINHAS = [
    r"por muito tempo eu ach",
    r"agora me conta aqui[,:]? qual",
    r"compartilha com quem merece ouvir isso hoje.{0,40}compartilha com quem merece",
    r"j[áa] salva esse v[íi]deo pra lembrar",
    r"sem pedir licen[çc]a",
    r"quietinho",
    r"n[ãa]o te avisa",
    r"a pergunta que eu passei a fazer",
    r"enfim, isso muda",
    # Plantado em duas clientes no mesmo dia, 21/09, e com zero ocorrencia na fala
    # das duas. Parece muleta de cliente e e' minha.
    r",\s*viu[,.?]",
]


def _palavras(t):
    return re.findall(r"[a-zà-ú']+", t.lower())


def varrer(roteiros, fontes_de_fala):
    fala = ' '.join(p.read_text(encoding='utf-8').lower() for p in fontes_de_fala)
    inteiro = {r['chave']: ' '.join([r['gancho'], r['corpo'], r['fechamento']]) for r in roteiros}
    reprova = []

    # 1. n-grama repetido que nao existe na fala dela
    ocorre = collections.defaultdict(set)
    for chave, texto in inteiro.items():
        w = _palavras(texto)
        for i in range(len(w) - 3):
            ocorre[' '.join(w[i:i + 4])].add(chave)
    repetidos = []
    for grama, chaves in ocorre.items():
        if len(chaves) > 1 and grama not in fala:
            repetidos.append((grama, sorted(chaves)))
    if repetidos:
        reprova.append(('repeticao minha dentro da leva', repetidos))

    # 2. construcao minha
    achados = []
    for chave, texto in inteiro.items():
        for padrao in MINHAS:
            if re.search(padrao, texto.lower(), re.S):
                achados.append((padrao, chave))
    if achados:
        reprova.append(('construcao minha proibida', achados))

    # 3. fechamento repetido
    fechos = collections.Counter(r['fechamento'] for r in roteiros)
    iguais = [(f, n) for f, n in fechos.items() if n > 1]
    if iguais:
        reprova.append(('fechamento repetido', iguais))

    return reprova, repetidos


def main(argv):
    from scripts import leva
    if len(argv) != 2:
        print('uso: .venv/bin/python -m scripts.varredura_repeticao <leva.json>', file=sys.stderr)
        return 2
    try:
        caminho = pathlib.Path(argv[1])
        dado = leva.ler(caminho)
        pasta = leva.pasta_da_leva(caminho)
        fontes = fala_do_cliente(pasta)
    except (ValueError, OSError) as erro:
        print(f'erro: {erro}', file=sys.stderr)
        return 2
    reprova, _ = varrer(dado['roteiros'], fontes)
    quantos = len(dado['roteiros'])
    if not reprova:
        print(f'passou ({pasta.name}, {quantos} roteiros): nenhuma repeticao minha, '
              f'nenhuma construcao proibida, {quantos} fechos distintos')
        return 0
    print(f'reprovou ({pasta.name}, {quantos} roteiros)')
    for titulo, itens in reprova:
        print(f'\n### {titulo}')
        for item in itens:
            print('   ', item)
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
