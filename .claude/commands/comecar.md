---
description: Comecar uma leva de roteiros, para voce ou para um cliente da assessoria
---

Voce conduz a pessoa do primeiro "oi" ate o link do Doc. Fale em portugues, curto,
uma pergunta por mensagem, e espere a resposta antes da proxima. Nunca use
travessao. Leia o `CLAUDE.md` antes de tudo.

## 0. Ambiente

Todo comando roda da raiz do repo, com o Python do `.venv` (sem ele, peca para
rodar `./instalar.sh`). Rode em silencio:

    .venv/bin/python -m pytest -q
    .venv/bin/python -m scripts.perfis

Teste vermelho: diga o que falhou e pare. Nada de gerar roteiro com o repo quebrado.

## 1. Abertura

Mande exatamente:

> Bem-vinda ao setor de roteiros da assessoria. Para quem você vai fazer os roteiros hoje?
> 1. Para você
> 2. Para os clientes da assessoria

Se `perfis` voltou com algum perfil, acrescente "3. Continuar com o seu perfil
(<nome>)". Com mais de um, liste cada um como opcao.

**Opcao 3:** pasta da leva = `perfis/<slug>` do perfil escolhido. Pergunte "Quantos
roteiros nessa leva? De 1 a 5." e va para a secao 3.

## 2a. Clientes da assessoria

Liste os `clientes` pelo `nome`, numerados. Depois que ela escolher, pergunte,
uma de cada vez:

1. "Tem um tema em mente, ou deixa que eu sugiro?"
2. "Quantos roteiros nessa leva? De 1 a 5."

Pasta da leva: `clientes/<slug>`. Siga para a secao 3.

## 2b. Para voce

Seis perguntas, uma por mensagem, nesta ordem. Pode reformular para soar natural,
mas nao junte duas numa mensagem.

1. "Qual o seu nome e o @ do seu Instagram? Vou puxar os reels em que você fala e
   transcrever, para pegar o seu jeito de falar."
2. "O que você faz e para quem você fala?"
3. "Qual dor ou desejo desse público você resolve? E o que você defende que os
   outros do seu nicho não defendem?"
4. "Que tipo de conteúdo você quer mais agora: ensinar algo útil, se posicionar,
   mostrar autoridade ou criar conexão? Pode misturar."
5. "Tem alguma referência? Perfis que você admira ou um texto seu, como legenda ou
   artigo. Uso só como estrutura, nunca copio."
6. "Seus roteiros citam estudo e dado científico, ou são mais de vivência? E tem
   algum assunto ou bandeira em que você não toca?"

**Antes de rodar a coleta** (logo depois da resposta 1, nesta ordem):

a. `<@perfil>`: se ela mandou um link (`instagram.com/fulana/...`), fique so' com
   `@fulana`. Calcule o slug uma vez e use esse em tudo:

       .venv/bin/python -c "import sys; from scripts import perfis; print(perfis.slug_de(sys.argv[1]))" "<nome>"

b. Se `clientes/<slug>` existe, pergunte "Qual o seu sobrenome?" e recalcule com
   nome e sobrenome.
c. Sem `~/.config/setor-de-roteiros/apify.env`, peca o token da Apify da assessoria
   (quem passa e' o responsavel pelo repo, nunca o chat de cliente) e grave:

       printf 'APIFY_TOKEN=%s\n' '<token>' > ~/.config/setor-de-roteiros/apify.env

d. Se `perfis/<slug>/reels.json` ou `transcricoes.md` ja existe, pergunte "Você já
   tem um perfil aqui. Quer que eu puxe os seus reels de novo?" Sim:
   `--sobrescrever` nos dois comandos. Nao: use o que esta la; se so' existe o
   `reels.json`, rode so' a transcricao.
e. Rode em segundo plano:

       mkdir -p "perfis/<slug>"
       .venv/bin/python -m scripts.coleta "perfis/<slug>" "<@perfil>" && .venv/bin/python -m scripts.transcricao "perfis/<slug>" "<@perfil>" "<nome>"

**Depois da transcricao.** A primeira linha do `perfis/<slug>/transcricoes.md` diz
quantos reels tem fala (`# Transcrições @x (N reels, ...)`). Com N abaixo de 10, ou
se a coleta parou por poucos videos, peca: "Me cola os links de reels em que você
fala?" Rode, com os links dela mais as URLs que ja estao no `transcricoes.md`:

    .venv/bin/python -m scripts.coleta_links "perfis/<slug>" <link> [<link> ...] --sobrescrever
    .venv/bin/python -m scripts.transcricao "perfis/<slug>" "<@perfil>" "<nome>" --sobrescrever

Transcricao vazia com mp4 baixado pode ser video sem audio: confira com `ffprobe`
e baixe de novo por cima, no mesmo nome, antes de rodar a transcricao com
`--sobrescrever`:

    .venv/bin/python -m yt_dlp -f "mp4/best" --force-overwrites -o "perfis/<slug>/mp4/<codigo>.mp4" "<url do reel>"

**Retrato.** Com as 6 respostas e a transcricao pronta, monte o retrato com:
`nome`, `slug` (o da etapa a), `instagram`, `voz` (marcas de fala reais, tiradas da
transcricao), `perfil`, `publico`, `dores_e_desejos`, `teses`, `tipos_de_conteudo`,
`referencias_dela`, `linha` ("cientifica" ou "vivencia"),
`bandeiras_que_nao_levanta`, `atualizado_em`. Mostre um resumo de 6 linhas e
pergunte "Está certo?". Corrija o que ela apontar. Confirmado, escreva o JSON num
arquivo temporario no scratchpad da sessao e grave:

    .venv/bin/python -c "import json,sys; from scripts import perfis; print(perfis.gravar_perfil(json.load(open(sys.argv[1]))))" <retrato.json>

Depois pergunte "Quantos roteiros nessa leva? De 1 a 5." Pasta da leva: `perfis/<slug>`.

## 3. Temas, e a primeira parada

Veja o que ja foi entregue:

    .venv/bin/python -c "import sys; from scripts import leva; print(*leva.temas_entregues(sys.argv[1]), sep='\n')" <pasta>

Proponha um tema por roteiro. Cada tema:

- sai da tese, das dores e do tipo de conteudo, com vivencia da pessoa primeiro;
- nao repete nada da lista acima, nem video que ela ja postou;
- com linha cientifica, traz dado com fonte conferida na web agora (link real);
- tem uma linha de sacada: o que o video revela.

Mostre a lista numerada com tema, sacada e fonte. Pergunte se pode escrever ou se
quer trocar algum. Nada e' escrito antes do sim.

## 4. Escrita

Para cada tema aprovado, com a chave `r1`, `r2`, ... na ordem da lista:

1. Escolha um molde em `base/ganchos-1005.json` que caiba no tema. Molde com
   `exige_fato: true` so' com fonte conferida. Na mesma leva, nenhum molde nem
   estrutura de abertura se repete.
2. Chame o agente `setor-roteirista` com a pasta, a chave, o tema, a sacada, a
   fonte, o molde e a saida `<pasta-temporaria>/<chave>.json`.
3. Chame o agente `setor-conferente` com a pasta e esse caminho.
4. Veredito nao: chame o roteirista de novo com os motivos. Segundo nao: troque o
   tema, avise a pessoa em uma linha e volte a secao 3 so' para esse roteiro.

Os roteiros de temas diferentes podem rodar em paralelo.

## 5. Varreduras

Junte os roteiros numa leva e grave (o comando imprime o `<leva.json>`):

    .venv/bin/python -c "import json,sys,datetime,pathlib; from scripts import leva; p=pathlib.Path(sys.argv[2]); print(leva.gravar({'nome':sys.argv[1],'slug':p.name,'data':datetime.date.today().isoformat(),'doc_url':'','roteiros':[json.load(open(a)) for a in sys.argv[3:]]}, p))" "<nome>" <pasta> <pasta-temporaria>/r1.json [<pasta-temporaria>/r2.json ...]

Rode:

    .venv/bin/python -m scripts.varredura_vicios <leva.json>
    .venv/bin/python -m scripts.varredura_repeticao <leva.json>
    .venv/bin/python -m scripts.varredura_copia <leva.json>

Codigos de saida:

- **2:** a leva ou a pasta esta errada (JSON invalido, fora de `<pasta>/levas/`,
  pasta sem `transcricoes.md` nem `reels.json`). Conserte o JSON ou a pasta; nao
  reescreva o script.
- **1:** reprovou. Corrija o texto do roteiro no `<leva.json>`, valide e regrave com
  o comando abaixo e rode de novo ate dar 0.
- **0:** passou.

A de vicios sai sempre com 0: a saida dela e' suspeita para ler. Leia cada uma e
corrija o que for vicio de verdade. Depois de toda correcao:

    .venv/bin/python -c "import sys; from scripts import leva; leva.atualizar(sys.argv[1], leva.ler(sys.argv[1]))" <leva.json>

## 6. Doc

Avise antes: "Vai abrir uma janela do Google para eu salvar o Doc no seu Drive."
Rode com timeout longo (10 minutos), porque o login espera o navegador:

    .venv/bin/python -m scripts.doc_em_abas <leva.json>

Sem `config/google-client.json`: diga que falta o setup do Google Cloud
(`docs/google-cloud.md`). Qualquer falha nesta etapa: nao commite, mostre os
roteiros no chat e diga em uma linha o que falhou.

## 7. Entrega

Mande o link do Doc e uma linha por roteiro (titulo e gancho). Nada mais.

Se a pasta for de cliente (`clientes/`), commite a leva. Antes, rode
`git status --porcelain --untracked-files=no`: se aparecer qualquer arquivo, pare
e diga a pessoa que ha mudancas no repo que nao sao desta leva. Limpo:

    git pull --rebase origin main
    git add <leva.json>
    git commit -m "<slug>: leva de <data>" -- <leva.json>
    git push origin main

Push recusado: `pull --rebase` e de novo. Conflito: pare e avise. Leva de perfil
nao vai pro git (a pasta e' ignorada).
