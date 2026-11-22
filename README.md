
<!-- /!\ Non OCA Context : Set here the badge of your runbot / runboat instance. -->
[![Pre-commit Status](https://github.com/kmee/l10n-brazil-sped/actions/workflows/pre-commit.yml/badge.svg?branch=16.0)](https://github.com/kmee/l10n-brazil-sped/actions/workflows/pre-commit.yml?query=branch%3A16.0)
[![Build Status](https://github.com/kmee/l10n-brazil-sped/actions/workflows/test.yml/badge.svg?branch=16.0)](https://github.com/kmee/l10n-brazil-sped/actions/workflows/test.yml?query=branch%3A16.0)
[![codecov](https://codecov.io/gh/kmee/l10n-brazil-sped/branch/16.0/graph/badge.svg)](https://codecov.io/gh/kmee/l10n-brazil-sped)
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
branch [`16.0-sped-base`](https://github.com/kmee/l10n-brazil/tree/16.0-sped-base) do
fork da KMEE. A lista está no [`test-requirements.txt`](test-requirements.txt), um addon
por linha (`odoo-addon-<addon> @ git+https://github.com/kmee/l10n-brazil@16.0-sped-base#subdirectory=<addon>`).

A branch é o OCA/l10n-brazil 16.0 com estes pull requests:

- OCA/l10n-brazil#5742: `l10n_br_sped_base` reescrito, com, por merge, a base dele
  (#5741 CST de entrada, #4965, #4966 e #4967 custo líquido, #5745 imposto sem crédito, e
  a marca e o assistente de encerramento do resultado no `l10n_br_account`);
- OCA/l10n-brazil#5749: código de receita e impostos retidos, usado pelo Y570 da ECF;
- as mudanças do `l10n_br_sped_base` dos pull requests da ECD (OCA/l10n-brazil#4948:
  signatários do J930, tela dos signatários e NIRE da empresa) e da EFD Contribuições
  (OCA/l10n-brazil#4924: registros montados em Python).

A branch também carrega versões de `l10n_br_sped_efd_icms_ipi`, `l10n_br_sped_ecd`,
`l10n_br_sped_ecf` e `l10n_br_tax_assessment`. O CI não as instala: esses módulos vêm
deste repositório, e só os addons listados no `test-requirements.txt` vêm do fork. Por
isso o job "Detect unreleased dependencies" do template acusa as linhas com URL: elas
saem quando cada addon for publicado no PyPI com a mudança.
Até lá, o vermelho desse job é esperado e não impede o merge.

O `pyopenssl` fica fixado em 22.1.0, como no `test-requirements.txt` do OCA/l10n-brazil
16.0: a imagem `oca-ci` traz uma `cryptography` antiga, e as versões novas do `pyopenssl`
exigem uma recente. Ele só entra como dependência de teste, e os módulos não usam as
funções de servidor TLS dos alertas de segurança; o Dependabot ignora o pacote.

## Documentação

- [Arquitetura](docs/ARQUITETURA.md): camadas, o que vem para cá e o que vai para o
  OCA/l10n-brazil, particularidades do CI.
- [Como contribuir](docs/CONTRIBUTING.md): fluxo, convenções, testes e portes.
- [AGENTS.md](AGENTS.md): orientações para agentes de IA.

Série: `16.0`; a `18.0` vem depois, por migração módulo a módulo. Repositórios irmãos:
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
[l10n_br_account_history](l10n_br_account_history/) | 16.0.1.0.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> | Historicos padrao com template de variaveis para as partidas dos lancamentos contabeis
[l10n_br_account_mapping](l10n_br_account_mapping/) | 16.0.1.0.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> | Mapeia as contas do Odoo para planos de contas externos: o plano do escritorio de contabilidade e o plano referencial da RFB
[l10n_br_account_mapping_sped](l10n_br_account_mapping_sped/) | 16.0.1.0.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> | Liga os planos de contas de destino ao plano referencial da RFB, base do registro I051 do SPED Contabil (ECD)
[l10n_br_account_mapping_sped_lucro_presumido](l10n_br_account_mapping_sped_lucro_presumido/) | 16.0.1.0.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> | Tabela oficial do plano referencial 2 da RFB (P100A, P150A, leiaute 12) para o registro I051 da ECD
[l10n_br_account_mapping_sped_lucro_real](l10n_br_account_mapping_sped_lucro_real/) | 16.0.1.0.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> | Tabela oficial do plano referencial 1 da RFB (L100A, L300A, leiaute 12) para o registro I051 da ECD
[l10n_br_account_move_template](l10n_br_account_move_template/) | 16.0.1.0.0 |  | Configurable double-entry accounting templates for Brazilian fiscal documents
[l10n_br_dctfweb](l10n_br_dctfweb/) | 16.0.1.0.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> | Assess the federal debits of the MIT and build its JSON file
[l10n_br_reinf](l10n_br_reinf/) | 16.0.1.0.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> | EFD-Reinf: withholding and other fiscal information for Brazil
[l10n_br_reinf_spec](l10n_br_reinf_spec/) | 16.0.1.0.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> | EFD-Reinf abstract models generated by xsdata-odoo from the official xsd
[l10n_br_sped_ecd](l10n_br_sped_ecd/) | 16.0.4.2.1 | <a href='https://github.com/rvalyi'><img src='https://github.com/rvalyi.png' width='32' height='32' style='border-radius:50%;' alt='rvalyi'/></a> <a href='https://github.com/renatonlima'><img src='https://github.com/renatonlima.png' width='32' height='32' style='border-radius:50%;' alt='renatonlima'/></a> | Arquivo ECD do SPED
[l10n_br_sped_ecf](l10n_br_sped_ecf/) | 16.0.1.0.0 | <a href='https://github.com/rvalyi'><img src='https://github.com/rvalyi.png' width='32' height='32' style='border-radius:50%;' alt='rvalyi'/></a> <a href='https://github.com/renatonlima'><img src='https://github.com/renatonlima.png' width='32' height='32' style='border-radius:50%;' alt='renatonlima'/></a> | Arquivo ECF do SPED
[l10n_br_sped_efd_icms_ipi](l10n_br_sped_efd_icms_ipi/) | 16.0.1.0.5 | <a href='https://github.com/rvalyi'><img src='https://github.com/rvalyi.png' width='32' height='32' style='border-radius:50%;' alt='rvalyi'/></a> <a href='https://github.com/renatonlima'><img src='https://github.com/renatonlima.png' width='32' height='32' style='border-radius:50%;' alt='renatonlima'/></a> | Arquivo EFD ICMS IPI do SPED / SPED Fiscal
[l10n_br_sped_efd_pis_cofins](l10n_br_sped_efd_pis_cofins/) | 16.0.1.0.0 | <a href='https://github.com/rvalyi'><img src='https://github.com/rvalyi.png' width='32' height='32' style='border-radius:50%;' alt='rvalyi'/></a> <a href='https://github.com/renatonlima'><img src='https://github.com/renatonlima.png' width='32' height='32' style='border-radius:50%;' alt='renatonlima'/></a> | Registros do EFD PIS COFINS do SPED
[l10n_br_sped_setup_tests](l10n_br_sped_setup_tests/) | 16.0.1.0.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> | Instala no CI o que os testes do SPED esperam do OCA/l10n-brazil completo
[l10n_br_tax_assessment](l10n_br_tax_assessment/) | 16.0.1.0.0 | <a href='https://github.com/mileo'><img src='https://github.com/mileo.png' width='32' height='32' style='border-radius:50%;' alt='mileo'/></a> | Conta gráfica mensal de ICMS, IPI, PIS e COFINS

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
<!-- /!\ Non OCA Context : Set here the full description of your organization. -->
