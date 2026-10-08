---
description: Comecar uma leva de roteiros, para voce ou para um cliente da assessoria
---

Voce conduz a pessoa do primeiro "oi" ate o link do Doc. Fale em portugues, curto,
uma pergunta por mensagem, e espere a resposta antes da proxima. Nunca use
travessao. Leia o `CLAUDE.md` antes de tudo.

## 0. Ambiente

Todo comando deste arquivo roda da raiz do repo (a pasta deste `CLAUDE.md`).
Rode em silencio:

    python3 -m pytest -q
    python3 -m scripts.perfis

Teste vermelho: diga o que falhou e pare. Nada de gerar roteiro com o repo quebrado.

## 1. Abertura

Mande exatamente:

> Bem-vinda ao setor de roteiros da assessoria. Para quem você vai fazer os roteiros hoje?
> 1. Para você
> 2. Para os clientes da assessoria

Se `perfis` voltou com algum perfil, acrescente "3. Continuar com o seu perfil
(<nome>)". Com mais de um, liste cada um como opcao.

## 2a. Clientes da assessoria

Liste os `clientes` pelo `nome`, numerados. Depois que ela escolher, pergunte,
uma de cada vez:

1. "Tem um tema em mente, ou deixa que eu sugiro?"
2. "Quantos roteiros nessa leva? De 1 a 5."

Pasta da leva: `clientes/<slug>`. Siga para o passo 3.

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

**Coleta em paralelo.** Assim que ela responder a 1, rode em segundo plano
(`<slug>` sai de `perfis.slug_de(<nome>)`):

    mkdir -p perfis/<slug>
    python3 -m scripts.coleta perfis/<slug> <@perfil> && python3 -m scripts.transcricao perfis/<slug> <@perfil> <nome>

Se `perfis/<slug>/transcricoes.md` ja existe (ela esta refazendo o perfil),
pergunte antes: "Você já tem um perfil aqui. Quer que eu puxe os seus reels de novo?"
Sim: acrescente `--sobrescrever` nos dois comandos. Nao: use a transcricao que esta la.

Sem `~/.config/setor-de-roteiros/apify.env`, peça o token da Apify da assessoria
(quem passa e' o responsavel pelo repo, nunca o chat de cliente) e grave a linha
`APIFY_TOKEN=<token>` nesse arquivo. Menos de 10 videos com fala: peca para ela
colar links de reels em que ela fala. Transcricao vazia com mp4 baixado pode ser
video sem audio: confira com `ffprobe` e baixe o audio com `yt-dlp` antes de
desistir.

**Retrato.** Com as 6 respostas e a transcricao pronta, monte o retrato com:
`nome`, `instagram`, `voz` (marcas de fala reais, tiradas da transcricao), `perfil`,
`publico`, `dores_e_desejos`, `teses`, `tipos_de_conteudo`, `referencias_dela`,
`linha` ("cientifica" ou "vivencia"), `bandeiras_que_nao_levanta`, `atualizado_em`.
Mostre um resumo de 6 linhas e pergunte "Está certo?". Corrija o que ela apontar.
Confirmado, escreva o JSON num arquivo temporario no scratchpad da sessao e grave
passando esse caminho:

    python3 -c "import json,sys; from scripts import perfis; print(perfis.gravar_perfil(json.load(open(sys.argv[1]))))" <retrato.json>

Depois pergunte "Quantos roteiros
nessa leva? De 1 a 5." Pasta da leva: `perfis/<slug>`.

## 3. Temas, e a primeira parada

Proponha um tema por roteiro. Cada tema:

- sai da tese, das dores e do tipo de conteudo, com vivencia da pessoa primeiro;
- nao repete nada de `leva.temas_entregues(<pasta>)`, nem video que ela ja postou;
- com linha cientifica, traz dado com fonte conferida na web agora (link real);
- tem uma linha de sacada: o que o video revela.

Mostre a lista numerada com tema, sacada e fonte. Pergunte se pode escrever ou se
quer trocar algum. Nada e' escrito antes do sim.

## 4. Escrita

Para cada tema aprovado:

1. Escolha um molde em `base/ganchos-1005.json` que caiba no tema. Na mesma leva,
   nenhum molde nem estrutura de abertura se repete.
2. Chame o agente `setor-roteirista` com a pasta, o tema, a sacada, a fonte, o
   molde e a saida `<pasta-temporaria>/<chave>.json`.
3. Chame o agente `setor-conferente` com a pasta e esse caminho.
4. Veredito nao: chame o roteirista de novo com os motivos. Segundo nao: troque o
   tema, avise a pessoa em uma linha e volte ao passo 3 so' para esse roteiro.

Os roteiros de temas diferentes podem rodar em paralelo.

## 5. Varreduras

Monte a leva (`nome`, `slug`, `data` de hoje, `doc_url` vazio, `roteiros`) e grave
com `leva.gravar(dado, <pasta>)`, que devolve o caminho `<leva.json>`. Rode:

    python3 -m scripts.varredura_vicios <leva.json>
    python3 -m scripts.varredura_repeticao <leva.json>
    python3 -m scripts.varredura_copia <leva.json>

Codigos de saida:

- **2:** a leva ou a pasta esta errada (JSON invalido, fora de `<pasta>/levas/`,
  pasta sem `transcricoes.md` nem `reels.json`). Conserte o JSON ou a pasta; nao reescreva o script.
- **1:** reprovou. Corrija o texto do roteiro, regrave com
  `leva.atualizar(<leva.json>, dado)` e rode de novo ate dar 0.
- **0:** passou.

A de vicios sai sempre com 0: a saida dela e' suspeita para ler. Leia cada uma e
corrija o que for vicio de verdade, regravando com `leva.atualizar`.

## 6. Doc

    python3 -m scripts.doc_em_abas <leva.json>

Na primeira vez abre o navegador para o login do Google: avise antes ("vai abrir
uma janela do Google para eu salvar o Doc no seu Drive"). Sem
`config/google-client.json`: diga que falta o setup do Google Cloud
(`docs/google-cloud.md`) e entregue os roteiros no chat por enquanto.

## 7. Entrega

Mande o link do Doc e uma linha por roteiro (titulo e gancho). Nada mais.

Se a pasta for de cliente (`clientes/`), commite a leva:

    git pull --rebase origin main
    git add <leva.json>
    git commit -m "<slug>: leva de <data>" -- <leva.json>
    git push origin main

Push recusado: `pull --rebase` e de novo. Conflito: pare e avise. Leva de perfil
nao vai pro git (a pasta e' ignorada).
