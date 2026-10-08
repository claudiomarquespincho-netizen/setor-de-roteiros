"""Varre uma leva inteira atras dos vicios de base/vicios.md.

Nao substitui o conferente: tres das onze regras pedem julgamento e nenhuma
expressao regular da conta delas. O que esta aqui e' o que da' para achar por
forma, e existe porque em 17/09 ele apontou vicio por vicio enquanto eu
consertava um de cada vez. A varredura ve os dez de uma vez, que e' como ele ve.

Marcacao e' suspeita, nao veredito: numero por extenso faz "cinquenta e oito"
parecer enumeracao de tres. Confira a mao o que ela marcar.

Uso: python3 -m scripts.varredura_vicios <leva.json>
"""

import collections
import pathlib
import re
import sys

SUSPEITAS = {
    "cauda de gancho": None,  # tratada a parte: e' estrutural, nao textual
    "diz como se sentir": [
        r"a resposta [^.?!]*(assusta|surpreend)", r"vai te surpreender",
        r"(voce|você) sabe (exatamente )?do que eu", r"sabe (exatamente )?do que eu (to|tô)",
        r"do jeito mais \w+ poss[ií]vel", r"olha (essa|esse|isso)",
        r"que a gente acha que", r"pouca gente sabe", r"quase ningu[ée]m (conta|sabe|lembra)",
        r"eu vou te mostrar", r"presta aten[çc][ãa]o",
    ],
    "comenta o proprio roteiro": [
        r"e (é|e) disso que eu (quero|vou) falar", r"vem a parte", r"que me ganhou",
        r"a parte que interessa", r"eu deixo pra voc[êe]",
        # 22/09, na v3 da Sandra: "E ai veio a parte que ninguem ve" e "Eu conto
        # isso porque" sao a mesma coisa em outro tempo verbal, e passaram.
        r"veio a parte", r"a parte que ningu[ée]m", r"eu conto isso porque",
    ],
    "anedota de consultorio vaga": [
        # 22/09, no r4 da Sandra: "esse tipo de frase e' horrivel". A frase
        # afirma a frequencia em vez de mostrar o caso, e quem ouve nao confere.
        r"eu vejo iss[oa] (toda|todo)", r"(toda semana|todo dia|todo m[êe]s) (chega|aparece|senta|eu vejo|vem)",
        r"(é|e) o que mais me traz", r"senta (aqui )?(na )?minha frente",
        r"eu atendo (muita|muitas|v[áa]rias)", r"chega (muita|muitas) (mulher|paciente)",
    ],
    "negativa espelhada": [
        # O par "nao X. X" e' a antitese vestida de duas frases. A regra de
        # vicios.md manda sair o par, e a negacao simples sozinha continua valendo.
        r"\bn[ãa]o (\w{3,})\b[^.?!]{0,90}[.?!]\s+(?:\w+\s+){0,2}\1\b",
        r"\b[Ee]u n[ãa]o \w+[^.?!]{0,90}[.?!]\s+Eu \w+",
    ],
    "numero por extenso": [
        # vicios.md: algarismo sempre, porque quem grava le na tela. Fora da lista
        # "um" e "uma", que sao artigo, e "mil", que e' como se escreve 10 mil.
        r"\b(dois|duas|tr[êe]s|quatro|cinco|seis|sete|oito|nove|dez|onze|doze|treze|"
        r"quinze|dezesseis|dezessete|dezoito|dezenove|vinte|trinta|quarenta|cinquenta|"
        r"sessenta|setenta|oitenta|noventa|cem|cento)\b",
    ],
    "hedge defensivo": [
        r"n[ãa]o (é|e) opini[ãa]o minha", r"eu sei que isso d[óo]i", r"claro que n[ãa]o",
        r"eu queria muito que fosse", r"muito pelo contr[áa]rio",
    ],
    "conselho retrospectivo": [r"mim mais nova", r"voltar no tempo", r"queria ter dito pra mim"],
    "antitese nao e X e Y": [r"[Nn][ãa]o (é|e) [^.?!]{4,70}\.\s*(Ele|Ela|É|E|Isso é)\s"],
}


# Muleta de fala que a pessoa tem de verdade. Sozinha ela e' a voz dela; a mesma
# no mesmo lugar em toda a leva e' a mao da maquina. Recado dele em 28/09 sobre
# a Sandra: "depois da primeira fala voce fala gente, em todos os videos".
MULETAS = ("gente", "tá?", "né?", "olha", "certo?", "bora", "galera")


def _tem(muleta, texto):
    # "gente" so' e' muleta como vocativo ("Isso foi medido, gente."). "A gente
    # devia" e "mandar gente embora" sao a lingua, e nao o tique.
    if muleta == "gente":
        return re.search(r",\s*gente\b|^gente\s*,|\bgente\s*[,!?:]\s", texto, re.I | re.M) is not None
    return re.search(r"(?<!\w)" + re.escape(muleta) + (r"" if muleta.endswith("?") else r"(?!\w)"),
                     texto, re.I) is not None


def muleta_repetida(roteiros, maximo_na_leva=2):
    """A mesma muleta logo depois do gancho em 2 roteiros, ou em mais de 2 da leva."""
    for muleta in MULETAS:
        no_comeco, na_leva = [], []
        for r in roteiros:
            frases = re.split(r"(?<=[.!?:])\s+", r["corpo"].strip())
            if _tem(muleta, " ".join(frases[:2])):
                no_comeco.append(r["chave"])
            if _tem(muleta, " ".join([r["gancho"], r["corpo"], r["fechamento"]])):
                na_leva.append(r["chave"])
        if len(no_comeco) >= 2:
            yield ", ".join(no_comeco), f"'{muleta}' logo depois do gancho"
        elif len(na_leva) > maximo_na_leva:
            yield ", ".join(na_leva), f"'{muleta}' em {len(na_leva)} roteiros"


def carregar(caminho):
    from scripts import leva
    return leva.ler(caminho)["roteiros"]


def cauda_de_gancho(roteiros):
    """Gancho com mais de uma frase nem sempre tem cauda, mas e' onde ela mora."""
    for r in roteiros:
        frases = [f.strip() for f in re.split(r"(?<=[.!?])\s+", r["gancho"]) if f.strip()]
        if len(frases) > 1:
            yield r["chave"], f"{len(frases)} frases, ultima: {frases[-1]!r}"


def transicao_repetida(roteiros, minimo=2):
    """Conector que abre paragrafo em roteiros diferentes da mesma leva."""
    onde = collections.defaultdict(set)
    for r in roteiros:
        for p in r["corpo"].split("\n\n"):
            onde[" ".join(p.split()[:3]).lower()].add(r["chave"])
    for abertura, chaves in sorted(onde.items()):
        if len(chaves) >= minimo:
            yield ", ".join(sorted(chaves)), f"{abertura}..."


def enumeracao_de_tres(texto, limite_de_palavras=8):
    """Lista de exatamente tres itens curtos, com ou sem o 'e' no fim.

    vicios.md: dois serve, quatro serve, tres nao. Regex nao conta item, entao
    aqui a frase e' quebrada na virgula e o ultimo pedaco ainda e' quebrado no
    'e', que e' como a enumeracao de tres costuma terminar.
    """
    for frase in re.split(r"(?<=[.!?])\s+", texto):
        # A virgula do decimal nao separa item: "1 a 1,2 grama por quilo" nao e
        # lista de tres. Medido na v8 da Sandra, onde 1,2 e 0,8 caiam aqui.
        partes = [p.strip() for p in re.split(r"(?<!\d),(?!\d)", frase) if p.strip()]
        if len(partes) < 2:
            continue
        itens = partes[:-1] + [x.strip() for x in re.split(r"\s+e\s+", partes[-1]) if x.strip()]
        # "Olha, ela e' uma ferramenta, e eu trabalho com ela" nao e' lista de
        # tres: o primeiro pedaco e' interjeicao. Vocativo no meio idem, como em
        # "Anota ai, gente, que e' facil". Pedaco de uma palavra so nao e' item.
        itens = [i for i in itens if len(i.split()) > 1]
        if len(itens) != 3:
            continue
        if any(len(i.split()) > limite_de_palavras for i in itens):
            continue
        yield frase.strip()


def por_expressao(roteiros):
    for r in roteiros:
        txt = " ".join([r["gancho"], r["corpo"], r["fechamento"]])
        for vicio, padroes in SUSPEITAS.items():
            for padrao in padroes or ():
                for achado in re.finditer(padrao, txt, re.I):
                    ini = max(0, achado.start() - 30)
                    yield vicio, r["chave"], f"…{txt[ini:achado.end() + 30]}…"
        for frase in enumeracao_de_tres(txt):
            yield "enumeracao de tres", r["chave"], frase


def main(caminho):
    roteiros = carregar(caminho)
    achados = 0

    print(f"== cauda de gancho ==  ({len(roteiros)} roteiros)")
    for chave, nota in cauda_de_gancho(roteiros):
        print(f"  {chave}: {nota}")
        achados += 1

    print("== transicao repetida na leva ==")
    for chaves, nota in transicao_repetida(roteiros):
        print(f"  {chaves}: {nota}")
        achados += 1

    print("== muleta repetida na leva ==")
    for chaves, nota in muleta_repetida(roteiros):
        print(f"  {chaves}: {nota}")
        achados += 1

    atual = None
    for vicio, chave, trecho in por_expressao(roteiros):
        if vicio != atual:
            print(f"== {vicio} ==")
            atual = vicio
        print(f"  {chave}: {trecho}")
        achados += 1

    print()
    print(f"{achados} suspeita(s). Nenhuma e' veredito: leia cada uma.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(pathlib.Path(sys.argv[1])))
