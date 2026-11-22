
<!-- /!\ Non OCA Context : Set here the badge of your runbot / runboat instance. -->
[![Pre-commit Status](https://github.com/kmee/l10n-brazil-sped/actions/workflows/pre-commit.yml/badge.svg?branch=18.0)](https://github.com/kmee/l10n-brazil-sped/actions/workflows/pre-commit.yml?query=branch%3A18.0)
[![Build Status](https://github.com/kmee/l10n-brazil-sped/actions/workflows/test.yml/badge.svg?branch=18.0)](https://github.com/kmee/l10n-brazil-sped/actions/workflows/test.yml?query=branch%3A18.0)
[![codecov](https://codecov.io/gh/kmee/l10n-brazil-sped/branch/18.0/graph/badge.svg)](https://codecov.io/gh/kmee/l10n-brazil-sped)
<!-- /!\ Non OCA Context : Set here the translation badge of your instance. -->

<!-- /!\ do not modify above this line -->

Escriturações do SPED e apuração de impostos para o Odoo, sobre o
[OCA/l10n-brazil](https://github.com/OCA/l10n-brazil).

Este repositório reúne os módulos que geram as escriturações digitais do SPED e o que
elas consomem:

- **escriturações**: EFD ICMS/IPI, EFD Contribuições (PIS/COFINS), ECD (escrituração
  contábil), ECF (escrituração contábil fiscal), EFD-Reinf e DCTFWeb;
- **apuração** dos impostos sobre consumo (`l10n_br_tax_assessment`), de onde saem o
  bloco E da EFD ICMS/IPI e o bloco M da EFD Contribuições;
- **plano de contas referencial e mapeamento contábil** da Receita Federal (lucro real e
  lucro presumido), histórico padrão e modelos de lançamento contábil, que a ECD e a ECF
  usam.

## O que fica no OCA/l10n-brazil

O `l10n_br_sped_base` (a máquina comum das escriturações: declaração, registros,
geração e importação do arquivo, signatários) e a base fiscal e contábil
(`l10n_br_fiscal`, `l10n_br_account`, planos de contas, estoque e compras) continuam no
OCA/l10n-brazil. Os módulos daqui dependem deles e nunca os alteram: o que a base
precisar muda por pull request no OCA/l10n-brazil.

## Por que um repositório separado

O CI do OCA/l10n-brazil instala e testa o repositório inteiro a cada pull request. Os
módulos do SPED estão entre os mais pesados da suíte: na medição de partida (21/11/2026,
job "test with Odoo" de um pull request com todo o SPED), eles levaram cerca de 17
minutos por rodada (EFD Contribuições 8,7 min, EFD ICMS/IPI 3,6, apuração 3,0, ECF 0,8,
EFD-Reinf 0,6, ECD 0,5), e cada pull request roda dois jobs de teste (Odoo e OCB). Aqui
eles são testados só quando mudam, e o CI do OCA/l10n-brazil fica mais leve para todo o
resto da localização.

O repositório é uma incubadora: segue o template, as licenças e as convenções da OCA
desde o primeiro commit, para poder ir para a organização da OCA, como o
[OCA/mis-builder-contrib](https://github.com/OCA/mis-builder-contrib).

## Dependências do OCA/l10n-brazil no CI

Enquanto os pull requests da base do SPED não forem mesclados e publicados no PyPI, o CI
instala do OCA/l10n-brazil só os addons de que os módulos daqui dependem, a partir da
branch [`18.0-sped-base-full`](https://github.com/kmee/l10n-brazil/tree/18.0-sped-base-full)
do fork da KMEE. A lista está no [`test-requirements.txt`](test-requirements.txt), um
addon por linha (`odoo-addon-<addon> @ git+https://github.com/kmee/l10n-brazil@18.0-sped-base-full#subdirectory=<addon>`).

A branch é o OCA/l10n-brazil 18.0 com os portes da base do SPED que ainda não foram
mesclados: o `l10n_br_sped_base` reescrito (porte do OCA/l10n-brazil#5742), o CST de
entrada (#5757, porte do #5741), a creditabilidade do imposto (#5764, porte do #4965), o
custo líquido no estoque e na compra (portes do #4966 e do #4967, sobre a migração do
`l10n_br_purchase_stock` do #5756), o imposto sem crédito no custo (porte do #5745), o
código de receita (#5759, porte do #5749), o contador do demo (#5761) e a marca e o
assistente de encerramento do resultado no `l10n_br_account`.

Só os addons listados no `test-requirements.txt` vêm do fork. Por isso o job "Detect
unreleased dependencies" do template acusa as linhas com URL: elas saem quando cada addon
for publicado no PyPI com a mudança. Até lá, o vermelho desse job é esperado e não impede
o merge.

O `requests_pkcs12` fica abaixo de 1.23 e o `signxml` em 3.2.2, como no OCA/l10n-brazil
18.0: a imagem `oca-ci` traz uma `cryptography` antiga, que as versões novas exigem mais
recente.

## Documentação

- [Arquitetura](docs/ARQUITETURA.md): camadas, o que vem para cá e o que vai para o
  OCA/l10n-brazil, particularidades do CI.
- [Como contribuir](docs/CONTRIBUTING.md): fluxo, convenções, testes e portes.
- [AGENTS.md](AGENTS.md): orientações para agentes de IA.

Séries: `16.0` e `18.0`. A `18.0` recebe os módulos por migração, módulo a módulo e com
histórico (16.0 -> 17.0 -> 18.0). Repositórios irmãos:
[kmee/l10n-brazil-fiscal-contrib](https://github.com/kmee/l10n-brazil-fiscal-contrib)
(documentos fiscais e grupos de nicho) e
[kmee/l10n-brazil-hr](https://github.com/kmee/l10n-brazil-hr) (recursos humanos).

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[l10n_br_account_history](l10n_br_account_history/) | 18.0.1.0.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> | Historicos padrao com template de variaveis para as partidas dos lancamentos contabeis
[l10n_br_account_mapping](l10n_br_account_mapping/) | 18.0.1.0.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> | Mapeia as contas do Odoo para planos de contas externos: o plano do escritorio de contabilidade e o plano referencial da RFB
[l10n_br_account_mapping_sped](l10n_br_account_mapping_sped/) | 18.0.1.0.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> | Liga os planos de contas de destino ao plano referencial da RFB, base do registro I051 do SPED Contabil (ECD)
[l10n_br_account_mapping_sped_lucro_presumido](l10n_br_account_mapping_sped_lucro_presumido/) | 18.0.1.0.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> | Tabela oficial do plano referencial 2 da RFB (P100A, P150A, leiaute 12) para o registro I051 da ECD
[l10n_br_account_mapping_sped_lucro_real](l10n_br_account_mapping_sped_lucro_real/) | 18.0.1.0.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> | Tabela oficial do plano referencial 1 da RFB (L100A, L300A, leiaute 12) para o registro I051 da ECD
[l10n_br_account_move_template](l10n_br_account_move_template/) | 18.0.1.0.0 |  | Configurable double-entry accounting templates for Brazilian fiscal documents
[l10n_br_sped_efd_icms_ipi](l10n_br_sped_efd_icms_ipi/) | 18.0.1.0.0 | <a href='https://github.com/rvalyi'><img src='https://github.com/rvalyi.png' width='32' height='32' style='border-radius:50%;' alt='rvalyi'/></a> <a href='https://github.com/renatonlima'><img src='https://github.com/renatonlima.png' width='32' height='32' style='border-radius:50%;' alt='renatonlima'/></a> | Arquivo EFD ICMS IPI do SPED / SPED Fiscal
[l10n_br_sped_setup_tests](l10n_br_sped_setup_tests/) | 18.0.1.0.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> | Instala no CI o que os testes do SPED esperam do OCA/l10n-brazil completo
[l10n_br_tax_assessment](l10n_br_tax_assessment/) | 18.0.1.0.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> | Conta gráfica mensal de ICMS, IPI, PIS e COFINS

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
<!-- /!\ Non OCA Context : Set here the full description of your organization. -->
