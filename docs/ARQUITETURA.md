# Arquitetura

Este repositório estende a localização brasileira do Odoo mantida pela OCA em
[OCA/l10n-brazil](https://github.com/OCA/l10n-brazil) com as escriturações do SPED e a
apuração de impostos. Ele nunca altera os módulos do OCA/l10n-brazil: todos os módulos
daqui dependem deles e os estendem por herança.

## Por que um repositório separado

O CI do OCA/l10n-brazil instala e testa o repositório inteiro a cada pull request. Os
módulos do SPED estão entre os mais lentos da suíte (cerca de 17 minutos por rodada do
job de teste, na medição de 21/11/2026), e cada pull request da localização paga esse
tempo, mesmo quando não toca o SPED. Num repositório próprio:

- o núcleo fica mais leve e o CI dele mais rápido;
- as escriturações têm revisão e ritmo de publicação próprios, que acompanham os
  leiautes da Receita Federal;
- quem não precisa delas não instala nem testa.

O repositório é uma incubadora, no mesmo espírito do
[OCA/mis-builder-contrib](https://github.com/OCA/mis-builder-contrib): segue o template
de addons, as licenças e as convenções da OCA desde o primeiro commit, para poder ser
levado inteiro para a organização da OCA.

## O que vem para cá e o que fica no OCA/l10n-brazil

| Mudança                                                                                    | Onde                             |
| ------------------------------------------------------------------------------------------ | -------------------------------- |
| Uma escrituração (registros, mapeamento a partir do Odoo, regras do PVA)                   | aqui, um módulo por escrituração |
| Apuração de impostos e o que as escriturações consomem dela                                | aqui                             |
| Plano referencial, mapeamento contábil, histórico padrão e modelos de lançamento           | aqui                             |
| Máquina comum das escriturações (`l10n_br_sped_base`)                                      | OCA/l10n-brazil                  |
| Campo, cadastro ou cálculo da base fiscal e contábil (`l10n_br_fiscal`, `l10n_br_account`) | OCA/l10n-brazil                  |

## Camadas

### Base (no OCA/l10n-brazil)

O `l10n_br_sped_base` define a declaração, os registros como modelos do Odoo gerados do
leiaute, a geração e a importação do arquivo, a assinatura e os signatários. Cada
escrituração herda dele os seus registros.

### Escriturações (`l10n_br_sped_<escrituração>`, `l10n_br_reinf`, `l10n_br_dctfweb`)

Cada módulo traz os modelos dos registros do leiaute vigente e o mapeamento de cada
registro a partir dos dados do Odoo (documentos fiscais, lançamentos, apuração). O
arquivo gerado é conferido no programa validador oficial (PVA) da escrituração.

### Apuração (`l10n_br_tax_assessment`)

Apura os impostos sobre consumo por período e por empresa, com ajustes e encerramento. A
EFD ICMS/IPI (bloco E), a EFD Contribuições (bloco M) e a DCTFWeb leem dela.

### Contabilidade (`l10n_br_account_mapping*`, `l10n_br_account_history`, `l10n_br_account_move_template`)

Plano referencial da Receita Federal por regime (lucro real e lucro presumido) e o
mapeamento do plano da empresa para ele, que a ECD e a ECF exigem; histórico padrão e
modelos de lançamento contábil.

## CI

O CI é o da OCA (imagens `oca-ci`). Ele instala só este repositório e as dependências
dele, o que traz consequências que o repositório principal não tem:

- os addons do OCA/l10n-brazil vêm da branch `16.0-sped-base` do fork da KMEE, listados
  um a um no `test-requirements.txt`, até que os pull requests da base sejam publicados
  no PyPI (veja o README);
- o `l10n_br_sped_setup_tests` é um módulo só de CI que instala o que os testes esperam
  encontrar no OCA/l10n-brazil completo: os planos de contas das empresas demo e das
  empresas de teste, o `l10n_br_stock_account` e o `l10n_br_nfe`.

## Séries

A `16.0` é a série em que os módulos nasceram, nos pull requests do OCA/l10n-brazil. A
`18.0` vem por migração módulo a módulo, e os pull requests da base que a 18.0 precisar
vão para o OCA/l10n-brazil 18.0.

## Ida para a OCA

Quando o repositório for para a OCA, o `copier update` troca o slug da organização e o
site do template, o repositório é transferido e entra nos projetos da localização no
[OCA/repo-maintainer-conf](https://github.com/OCA/repo-maintainer-conf).
