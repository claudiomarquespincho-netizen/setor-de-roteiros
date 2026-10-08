"""Transcreve os mp4 da coleta com o Whisper, na maquina dela.

A lista de palavras do cliente vai no `--initial_prompt` porque sem ela a marca
sai "Xerri" ou "Cheri", scrub sai "Scrabby" e jaleco sai "aleco". Nome de marca
errado no retrato vira nome de marca errado no roteiro, e e' o tipo de erro que
ela ve no primeiro segundo.

Medido em 2026-09-17: 9 min 15 s de transcricao para uns 44 min de audio, no
modelo medium. Trocar por mlx-whisper, que usa a GPU do M2, ficou de fora desta
etapa de proposito.

Video sem fala nao entra no documento: ele nao ensina voz nenhuma, e contar um
video muvido como se fosse fala inflaria a conta de 10 videos minimos.
"""

import pathlib
import re
import subprocess
import sys

MODELO = "medium"
TAMANHO_MINIMO_DE_PALAVRA = 5

# O que o Whisper escreve quando nao tem fala nenhuma: ele preenche o silencio
# com bordao de legenda de YouTube. Medido em 2026-09-20, na coleta da Sandra:
# 2 dos 28 reels sairam so' com isso, e o documento contava os dois como voz
# dela. Voz que nao e' dela e' pior do que video mudo, porque o retrato copia.
ALUCINACAO = (
    "inscreva-se no canal",
    "inscreva-se no nosso canal",
    "ative o sininho",
    "legendas pela comunidade",
    "amara.org",
    "obrigado por assistir",
)

# Abaixo disso nao da' para tirar jeito de falar de ninguem: sao as pontas de
# audio que sobram de reel de musica com uma palavra solta no meio.
PALAVRAS_MINIMAS_DE_FALA = 12


CAMPOS_DO_REEL = ("quando", "segundos", "views", "url", "codigo")


def prompt_inicial(palavras):
    """As palavras do cliente numa frase, que e' o formato que o Whisper aceita.

    Recusa lista vazia em vez de mandar "Vocabulario: ." para o Whisper. A dica
    vazia nao dica nada, e o passo todo existe porque sem ela a marca sai errada:
    seguir calado seria transcrever 44 minutos de audio para jogar fora.
    """
    if not palavras:
        raise ValueError(
            "sem palavras do cliente: a transcrição sairia com a marca errada")
    return "Vocabulário: " + ", ".join(palavras) + "."


def comando(mp4, saida, palavras, modelo=MODELO):
    """O whisper pelo modulo, e nao pelo console script.

    Em 2026-09-20, na coleta da Sandra, `whisper` nao estava no PATH e as 28
    transcricoes morreram num FileNotFoundError depois da coleta inteira ter
    rodado. O modulo estava instalado o tempo todo. Chamar por
    `sys.executable -m whisper` usa o mesmo Python que roda a esteira, e nao
    depende de onde o pip pendurou o atalho.
    """
    return [sys.executable, "-m", "whisper", str(mp4), "--language", "pt", "--model", modelo,
            "--output_format", "txt", "--output_dir", str(saida),
            "--initial_prompt", prompt_inicial(palavras)]


def palavras_das_legendas(reels, minimo=TAMANHO_MINIMO_DE_PALAVRA):
    """Um primeiro palpite de vocabulario, tirado das legendas dos proprios reels.

    E' palpite mesmo: quem fecha a lista e' quem olha o retrato com ela. Serve
    para a primeira transcricao nao sair com a marca errada.
    """
    achadas = []
    for reel in reels:
        for palavra in re.findall(r"[A-Za-zÀ-ÿ]+", reel.get("legenda") or ""):
            if len(palavra) >= minimo and palavra not in achadas:
                achadas.append(palavra)
    return achadas


def cabecalho(reel):
    """A linha que abre o bloco de um reel no documento.

    Confere os campos antes de formatar, e diz qual reel esta torto. Formatar
    direto levantaria `KeyError` com o nome do campo e nada mais, e quem le a
    falha precisa saber de qual dos vinte e um videos se trata.
    """
    faltando = [campo for campo in CAMPOS_DO_REEL if campo not in reel]
    if faltando:
        raise ValueError(
            f"reel {reel.get('codigo') or reel.get('url') or 'sem identificação'} "
            f"sem {', '.join(faltando)}")
    return (f"## {reel['quando']} · {reel['segundos']} s · {reel['views']} views\n"
            f"{reel['url']}")


def parece_fala(texto, minimo=PALAVRAS_MINIMAS_DE_FALA):
    """Se o que saiu do Whisper ensina voz, ou se e' silencio preenchido.

    Nao separa musica de fala: isso e' julgamento de quem le, e a coleta da
    Sandra mostrou que so' o olho separa letra de musica de fala da pessoa. O
    que da' para fazer por forma e' recusar o vazio, o bordao e a frase solta.
    """
    limpo = (texto or "").strip()
    if not limpo:
        return False
    baixo = limpo.lower()
    if any(frase in baixo for frase in ALUCINACAO) and len(limpo.split()) < 40:
        return False
    return len(limpo.split()) >= minimo


def montar(perfil, reels, textos):
    """O documento que a pessoa le, e de onde sai o retrato.

    Confere todos os reels antes de montar linha nenhuma, porque documento pela
    metade e' pior que erro: alguem leria o que saiu como se fosse a coleta
    inteira.
    """
    for reel in reels:
        cabecalho(reel)
    com_fala = [r for r in sorted(reels, key=lambda r: r["quando"], reverse=True)
                if parece_fala(textos.get(r["codigo"]))]
    mudos = len(reels) - len(com_fala)
    datas = sorted(r["quando"] for r in com_fala) or ["sem data"]
    linhas = [f"# Transcrições {perfil} ({len(com_fala)} reels, "
              f"{datas[0]} a {datas[-1]})", ""]
    if mudos:
        linhas += [f"{mudos} vídeo sem fala ficou de fora: não ensina voz nenhuma.", ""]
    linhas += ["Transcrição automática pelo Whisper. Confira nome de marca e termo do "
               "nicho antes de usar no retrato.", ""]
    for reel in com_fala:
        linhas += [cabecalho(reel), "", textos[reel["codigo"]].strip(), ""]
    return "\n".join(linhas)


def transcrever(mp4, saida, palavras, rodar=None):
    """Chama o Whisper e devolve o texto do .txt que ele escreveu."""
    rodar = rodar or subprocess.run
    pasta = pathlib.Path(saida)
    pasta.mkdir(parents=True, exist_ok=True)
    rodar(comando(mp4, pasta, palavras), check=True)
    txt = pasta / (pathlib.Path(mp4).stem + ".txt")
    return txt.read_text(encoding="utf-8") if txt.exists() else ""


def main(argv):
    import json
    if len(argv) < 3:
        print("uso: <pasta do cliente ou perfil> <@perfil> [palavra extra] ...")
        return 1
    raiz, perfil = pathlib.Path(argv[1]), argv[2]
    reels = json.loads((raiz / "reels.json").read_text(encoding="utf-8"))
    palavras = palavras_das_legendas(reels) + list(argv[3:])
    textos = {}
    for reel in reels:
        mp4 = raiz / "mp4" / f"{reel['codigo']}.mp4"
        if not mp4.exists():
            continue
        textos[reel["codigo"]] = transcrever(mp4, raiz / "txt", palavras)
    documento = raiz / "transcricoes.md"
    documento.write_text(montar(perfil, reels, textos), encoding="utf-8")
    print(f"{len(textos)} transcritos em {documento}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
