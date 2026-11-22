# AGENTS.md

Orientações para agentes de IA que trabalham neste repositório. Pessoas devem ler o
[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) e o
[docs/ARQUITETURA.md](docs/ARQUITETURA.md); este arquivo resume o que um agente precisa
e acrescenta as armadilhas que já custaram rodadas de CI. O `CLAUDE.md` é um link para
este arquivo.

## O que é este repositório

Addons do Odoo para as escriturações do SPED e a apuração de impostos, sobre o
[OCA/l10n-brazil](https://github.com/OCA/l10n-brazil), no template de addons da OCA:

- `l10n_br_sped_<escrituração>`: uma escrituração (EFD ICMS/IPI, EFD Contribuições, ECD,
  ECF), sobre a máquina do `l10n_br_sped_base`, que fica no OCA/l10n-brazil;
- `l10n_br_reinf_spec` e `l10n_br_reinf`: EFD-Reinf (modelos gerados do XSD e eventos);
- `l10n_br_dctfweb`: DCTFWeb a partir da apuração;
- `l10n_br_tax_assessment`: apuração dos impostos sobre consumo;
- `l10n_br_account_mapping*`, `l10n_br_account_history`,
  `l10n_br_account_move_template`: plano referencial da Receita Federal, mapeamento
  contábil, histórico padrão e modelos de lançamento;
- `l10n_br_sped_setup_tests`: só para o CI, instala o que os testes esperam do
  OCA/l10n-brazil completo (planos de contas, `l10n_br_stock_account`, `l10n_br_nfe`).

Série: `18.0`. As dependências do OCA/l10n-brazil vêm da branch `18.0-sped-base-full` do
fork `kmee/l10n-brazil`, listadas uma a uma no `test-requirements.txt` (veja o README).
Nunca altere esses addons a partir daqui: mudança na base é pull request no
OCA/l10n-brazil, e depois a branch do fork é atualizada.

## Regras

- Não invente regra fiscal, código, registro ou data. Todo registro segue o leiaute
  oficial (o descritor do programa validador, o PVA, vale mais que o Guia Prático em
  PDF); o que não puder ser confirmado vai para o `readme/ROADMAP.md`.
- Um módulo por pull request, um commit por módulo sempre que possível.
- Mensagem de commit: `[ADD|FIX|IMP|MIG|REF] <módulo>: <resumo>` em inglês, mais o
  trailer `Assisted-by: <nome da ferramenta>`. Nunca acrescente `Co-authored-by` de
  ferramenta de IA.
- Não suba a versão de um módulo existente. Módulo novo começa em `<série>.1.0.0`,
  licença AGPL-3, autor `<empresa>, Odoo Community Association (OCA)`.
- Edite os fragmentos `readme/*.md`, nunca o `README.rst` ou o
  `static/description/index.html`, que o pre-commit gera. Código e comentários no código
  ficam em inglês.
- Nunca edite à mão os arquivos gerados dos módulos de spec; regere como o readme do
  spec descreve.
- Arquivos da raiz (`test-requirements.txt`, `.pre-commit-config.yaml`,
  `requirements.txt`, o módulo de setup) são compartilhados: mude-os num pull request
  próprio. O `requirements.txt` só muda pelo hook do pre-commit, a partir do
  `external_dependencies` declarado pelo nome.
- Nenhum dado real de contribuinte (CNPJ, CPF, nome, endereço) em código, teste ou dado
  de demonstração.
- Teste nunca chama webservice real: simule o transporte.
- Em texto e comentário, use pontuação ASCII simples (sem travessão tipográfico, aspas
  curvas ou caractere de reticências).

## Comandos

```bash
pre-commit run --all-files        # rode duas vezes: a primeira regera os readmes
```

Os testes rodam no CI (imagens `oca-ci`, jobs `test with Odoo` e `test with OCB`). Para
rodar localmente, use a mesma imagem com um PostgreSQL descartável, passando os addons a
testar; apague os containers ao terminar e nunca deixe volume anônimo do Docker para
trás (o PostgreSQL declara um volume: dê nome a ele).

## Armadilhas de CI já pagas

- O banco do CI tem só este repositório e as dependências dele. Os testes do SPED
  nasceram no CI do OCA/l10n-brazil, que instala tudo: sem o módulo de setup, as
  empresas demo ficam sem plano de contas, os testes de entrada sem crédito são pulados
  (falta o `l10n_br_stock_account`) e a NF-e de venda dos testes recusa a chave de
  acesso de uma empresa sem CNPJ (falta o `l10n_br_nfe`).
- Um addon do OCA/l10n-brazil que não está no `test-requirements.txt` vem do PyPI, na
  versão publicada, e pode não combinar com os que vêm do fork. Ao acrescentar uma
  dependência do OCA/l10n-brazil num manifest, acrescente a linha dela também.
- A branch do fork carrega módulos que moram aqui (`l10n_br_sped_efd_icms_ipi`,
  `l10n_br_sped_ecd`, `l10n_br_sped_ecf`, `l10n_br_tax_assessment`). Nunca os liste no
  `test-requirements.txt`: o addon passaria a vir do fork, e não deste repositório.
- CI verde pode significar que nada rodou: confira no log que os testes do módulo
  começaram e passaram.
- Um PR verde sozinho pode quebrar a base junto com os outros módulos: rebaseie sobre a
  branch atualizada antes do merge e confira o CI de novo.

## Por onde começar

1. Leia o [docs/ARQUITETURA.md](docs/ARQUITETURA.md).
2. Veja o `l10n_br_sped_efd_icms_ipi` (escrituração com registros gerados do leiaute e
   mapeamento a partir do Odoo) e o `l10n_br_tax_assessment` (apuração).
3. Procure no OCA/l10n-brazil um módulo ou pull request aberto antes de escrever código.
