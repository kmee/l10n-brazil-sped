# Como contribuir

Contribuições são bem-vindas. O repositório segue as
[diretrizes de contribuição da OCA](https://github.com/OCA/odoo-community.org/blob/master/website/Contribution/CONTRIBUTING.rst),
porque vai ser levado para a organização da OCA. Leia antes o
[ARQUITETURA.md](ARQUITETURA.md): ele explica o que pertence a este repositório e o que
pertence ao [OCA/l10n-brazil](https://github.com/OCA/l10n-brazil).

## Antes de começar

1. Procure nas issues e nos pull requests deste repositório e do OCA/l10n-brazil.
2. Encontre a fonte oficial do que você vai implementar: o leiaute da escrituração (o
   descritor do PVA vale mais que o Guia Prático em PDF), as notas técnicas e a
   legislação. Regra fiscal nunca é suposta: o que não puder ser confirmado vai para o
   roadmap do módulo.
3. Se a mudança precisa da base (`l10n_br_sped_base`, `l10n_br_fiscal`,
   `l10n_br_account`), ela vai primeiro para um pull request no OCA/l10n-brazil.

## Pull requests

- Um módulo por pull request.
- Nome da branch: `<série>-add-<módulo>` para módulo novo, `<série>-mig-<módulo>` para
  porte, `<série>-fix-<módulo>-<assunto>` para correção.
- Título do pull request: `[<série>][ADD|FIX|IMP|MIG] <módulo>: <resumo>`.
- Mensagem de commit no padrão da OCA: `[ADD] <módulo>: <resumo>`, sem a série. Não suba
  a versão de um módulo existente.
- Módulo novo começa na versão `<série>.1.0.0`, licença AGPL-3 e autor
  `<Sua empresa>, Odoo Community Association (OCA)`.
- Biblioteca Python importada em tempo de execução vai em `external_dependencies` no
  manifest, só pelo nome; o hook do pre-commit regera o `requirements.txt`.
- Dependência nova do OCA/l10n-brazil entra também no `test-requirements.txt`, enquanto
  o CI instalar a base do fork.

## Código e testes

- Rode `pre-commit run --all-files` até passar. Ele gera o `README.rst` e o
  `static/description/index.html` a partir dos fragmentos em `readme/`: edite os
  fragmentos, nunca os arquivos gerados.
- Nunca edite à mão os arquivos gerados dos registros do leiaute. Regere como descrito
  no readme do módulo.
- Testes pequenos e rápidos: monte o cenário, gere o arquivo e confira os registros que
  você implementou. Teste nunca chama webservice real.
- Nunca use dados reais de contribuinte. CNPJ e CPF de teste não podem colidir com os
  dados de demonstração do OCA/l10n-brazil.

## Assistência de IA

Siga a
[política da OCA sobre contribuições com IA](https://odoo-community.org/blog/news-updates-1/new-ai-policy-248):
quem contribui responde pela mudança e a revisa antes de enviar, commit feito com
assistência de IA leva o trailer `Assisted-by:`, e ferramenta de IA nunca aparece como
coautora. O [AGENTS.md](../AGENTS.md) descreve o repositório para agentes de código.

## Depois do merge

A tabela de módulos do `README.md` da raiz é gerada pelo `oca-gen-addons-table`, do
[OCA/maintainer-tools](https://github.com/OCA/maintainer-tools). Rode quando um pull
request acrescentar ou retirar módulo.

## Licença e CLA

As contribuições são licenciadas sob AGPL-3. Como o repositório vai para a OCA, pedimos
que quem contribui assine o
[Contributor License Agreement da OCA](https://odoo-community.org/page/cla).
