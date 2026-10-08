# Setor de Roteiros

Este repositorio escreve roteiros de video curto para os clientes da assessoria e
para quem usa o repo. Comece sempre por `/comecar`.

## As regras que nao mudam

1. **Nenhum fato fabricado.** Sem fonte, versao generica e verdadeira. Integridade
   vence roteiro bonito.
2. **Nenhum roteiro sai sem a pessoa aprovar os temas antes.**
3. **A voz e' da pessoa.** A transcricao ensina como ela fala. Nunca vira tema, e
   frase dela que ja foi ao ar nao volta.
4. **Referencia e' estrutura, nunca texto.** A varredura de copia confere.
5. **Nenhum travessao**, em roteiro, Doc ou chat.
6. **Cautela dobrada** em saude, saude mental e financas. O `cuidado` do retrato e' lei.
7. **Uma mensagem por roteiro:** historia, ensinamento e chamada dizem a mesma coisa.

## Onde fica cada coisa

- `clientes/<slug>/`: retrato, regras, transcricoes e levas dos clientes da assessoria.
- `perfis/<slug>/`: o "para voce" de quem usa esta maquina. O git ignora.
- `base/`: os 1005 ganchos, os vicios de IA, as regras gerais, os roteiros de referencia.
- `scripts/`: coleta, transcricao, varreduras e o Doc em abas. Tudo tem teste.

## Antes de mexer no codigo

- `python3 -m pytest -q` antes e depois.
- Commit sempre com caminho: `git commit -m "..." -- <caminhos>`.
- Cliente novo da assessoria nao se cadastra aqui: quem cadastra e' o responsavel
  pelo repo, na bancada, e traz pronto.
- Segredo nenhum entra no repo. Token da Apify e login do Google moram em
  `~/.config/setor-de-roteiros/`.
