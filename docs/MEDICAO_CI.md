# Medição do CI do OCA/l10n-brazil com e sem os módulos do SPED

Feita em 22 e 23/11/2026 para a proposta na OCA/l10n-brazil#5727.

Objetivo: medir quanto o job de teste do OCA/l10n-brazil ganha se os módulos do SPED saírem para
`kmee/l10n-brazil-sped` (público), ficando no l10n-brazil só o `l10n_br_sped_base`. As rodadas foram feitas em branches novas do fork `kmee/l10n-brazil`, no CI
hospedado do GitHub (mesmo workflow `tests` da OCA, imagens oca-ci).

## Resumo

- **16.0 hoje:** saem `l10n_br_sped_ecd`, `l10n_br_sped_ecf` e `l10n_br_sped_efd_icms_ipi`. O ganho é
  pequeno: cerca de **0,6 a 0,7 min por job (1,6 a 1,8%)**, porque esses módulos hoje têm só 11 testes.
- **16.0 com os PRs abertos do SPED** (#5742, #4924, #4948, #4877, #4882, #4931, #4992): eles
  acrescentariam **18,1 min ao job "test with Odoo" e 14,6 min ao "test with OCB"** (mais 455 testes).
  Tirar o SPED do l10n-brazil evita esse acréscimo: o job Odoo iria de cerca de 57,5 min para 38,8 min
  (**menos 18,7 min, 32%**), o OCB de 50,6 para 35,4 min estimados (**menos 15,2 min, 30%**).
- **18.0 hoje:** só existe o `l10n_br_sped_base`, que fica. Não há o que tirar: ganho zero. O que pesa
  na 18.0 é o próprio `sped_base` (1,4 a 1,7 min no job Odoo), atacado pelo OCA/l10n-brazil#5775
  (testes do sped_base de 83 a 104 s para 8 s no job Odoo, cerca de 1,5 min a menos).
- **18.0 com os módulos migrados** (só referência, runner próprio): ordem de grandeza igual à 16.0,
  cerca de 15 min a mais por job se entrassem no l10n-brazil.
- **Nenhum módulo que fica depende dos que saem** (16.0, 18.0 e heads dos 7 PRs).
- **Ruído do CI hospedado é maior que o efeito atual:** o mesmo código variou até 10 min entre
  rodadas (a velocidade da máquina variou até 2 vezes). Por isso o ganho atual vem do tempo por
  módulo medido no log, conferido pela duração normalizada pela velocidade da máquina.

## Módulos que saem e dependências

| Módulo | origin/16.0 | origin/18.0 | Onde está |
|---|---|---|---|
| l10n_br_sped_base | sim | sim | fica no l10n-brazil |
| l10n_br_sped_ecd | sim | não | sai (PR #4948 na 16.0) |
| l10n_br_sped_ecf | sim | não | sai (PR #4877 na 16.0) |
| l10n_br_sped_efd_icms_ipi | sim | não | sai (PR #5742 na 16.0) |
| l10n_br_sped_efd_pis_cofins | não | não | só em PR (#4924) |
| l10n_br_tax_assessment | não | não | só em PR (#4882; também no stack do #5742) |
| l10n_br_reinf_spec, l10n_br_reinf | não | não | só em PR (#4931) |
| l10n_br_dctfweb | não | não | só em PR (#4992) |

Dependências: `git grep` nos `__manifest__.py` de `origin/16.0`, `origin/18.0` e dos heads dos 7 PRs
não encontrou nenhum módulo que fica dependendo de um que sai. As únicas citações aos módulos que
saem fora deles são texto (README da raiz, metapackage em `setup/_metapackage`, readme e `.pot` do
`l10n_br_sped_base`). Na branch sem SPED foram removidos as pastas, os `setup/<módulo>`, as linhas do
metapackage e as linhas da tabela do README.

## 16.0: com e sem SPED (estado atual do origin/16.0)

Base: OCA/l10n-brazil 16.0 em `1c2799fe13`. Três rodadas de cada lado, as duas branches disparadas
juntas em cada rodada (22:51, 23:35 e 00:19 UTC, 22 e 23/11/2026). Tempos em minutos.

| Job | Com SPED (média) | Sem SPED (média) | Diferença bruta | Diferença medida (módulos que saem) | % do job |
|---|---|---|---|---|---|
| test with Odoo | 39,4 (43,2 / 41,9 / 33,0) | 37,6 (41,2 / 31,5 / 40,1) | -1,8 (ruído) | **-0,65** | **1,6%** (normalizado 1,8%) |
| test with OCB | 36,0 (34,8 / 40,5 / 32,8) | 27,7 (30,6 / 21,6 / 30,8) | -8,3 (ruído) | **-0,57** | **1,6%** (normalizado 1,6%) |

Detalhe por etapa (média das 3 rodadas, job Odoo; OCB entre parênteses):

| Etapa | Com SPED | Sem SPED |
|---|---|---|
| Instalação (`oca_install_addons`) | 1,1 (1,1) | 1,1 (0,9) |
| Banco de teste (`oca_init_test_database`) | 1,7 (1,5) | 1,7 (1,1) |
| `oca_run_tests` inteiro | 35,2 (32,1) | 33,5 (24,5) |
| Carga dos módulos com testes at_install | 23,6 (21,4) | 22,4 (16,4) |
| Testes post_install | 11,2 (10,3) | 10,8 (7,8) |
| Módulos carregados | 233 (210) | 230 (207) |
| Testes (`tests.result`) | 1539 | 1534 |
| Testes nos módulos que saem (`tests.stats`) | 11 (ecd 3, ecf 3, efd_icms_ipi 5) | 0 |

Tempo dos módulos que saem (média das 3 rodadas, job Odoo): efd_icms_ipi 0,30, ecf 0,20, ecd 0,15
(soma 0,65); o `sped_base` fica, com 0,07.

## 16.0: o que os PRs abertos do SPED acrescentariam

Tempo por módulo no log do CI de cada PR na OCA (head atual), menos o tempo que o
mesmo módulo já leva hoje (média das 3 rodadas com SPED). Minutos por job.

| Módulo | PR (run na OCA) | Testes | Odoo no PR | Odoo hoje | Acréscimo Odoo | Acréscimo OCB |
|---|---|---|---|---|---|---|
| l10n_br_sped_efd_pis_cofins | #4924 ([44884875617](https://github.com/OCA/l10n-brazil/actions/runs/44884875617)) | 118 | 8,73 | 0 | 8,73 | 6,52 |
| l10n_br_sped_efd_icms_ipi | #5742 ([45011405046](https://github.com/OCA/l10n-brazil/actions/runs/45011405046)) | 78 | 4,73 | 0,30 | 4,43 | 3,21 |
| l10n_br_tax_assessment | #4882 ([44770564379](https://github.com/OCA/l10n-brazil/actions/runs/44770564379)) | 79 | 2,96 | 0 | 2,96 | 2,99 |
| l10n_br_sped_ecf | #4877 ([44949575544](https://github.com/OCA/l10n-brazil/actions/runs/44949575544)) | 27 | 0,78 | 0,20 | 0,58 | 0,59 |
| l10n_br_reinf + reinf_spec | #4931 ([36515549362](https://github.com/OCA/l10n-brazil/actions/runs/36515549362)) | 49 | 0,59 | 0 | 0,59 | 0,51 |
| l10n_br_sped_ecd | #4948 ([44949571423](https://github.com/OCA/l10n-brazil/actions/runs/44949571423)) | 23 | 0,54 | 0,15 | 0,39 | 0,40 |
| l10n_br_dctfweb | #4992 ([37020542116](https://github.com/OCA/l10n-brazil/actions/runs/37020542116)) | 92 | 0,38 | 0 | 0,38 | 0,38 |
| **Total** | | **466** (hoje 11) | | | **18,1** | **14,6** |

Confere com a referência de 21/11 (EFD Contribuições 8,7, EFD ICMS/IPI 3,6 a 4,7, apuração 3,0,
ECF 0,8, Reinf 0,6, ECD 0,5).

Projeção da 16.0 com todos os PRs mesclados:

| Job | Com SPED e os PRs | Sem SPED | Ganho | % |
|---|---|---|---|---|
| test with Odoo | 57,5 (39,4 + 18,1) | 38,8 (39,4 - 0,65) | **18,7** | **32%** |
| test with OCB | 50,6 (36,0 + 14,6) | 35,4 (36,0 - 0,6) | **15,2** | **30%** |

A coluna "sem SPED" usa a média com SPED menos o ganho medido por módulo, e não a média bruta das
rodadas sem SPED (37,6 e 27,7), que carrega o ruído da máquina sorteada (ver abaixo).

Custo do outro lado: no `kmee/l10n-brazil-sped` (16.0, CI hospedado, PR #1 de 21/11) o job inteiro
com todos esses módulos leva 19,0 a 22,0 min, e só roda em PR do SPED. Lá cada módulo é mais rápido
que dentro do l10n-brazil (EFD Contribuições 5,6 contra 8,7 min; EFD ICMS/IPI 2,6 contra 4,7), porque
o banco tem 96 módulos em vez de 233.

## 18.0

Base: OCA/l10n-brazil 18.0 em `29ac3afb02`. Só existe o `l10n_br_sped_base`, que fica: a branch sem
SPED seria idêntica, então só a linha de base foi rodada, duas vezes (serve também de medida de ruído).

| Job | Rodada 1 (22:51) | Rodada 2 (23:52) | Média | Sem SPED | Diferença |
|---|---|---|---|---|---|
| test with Odoo | 59,7 | 46,4 | 53,1 | igual | 0 |
| test with OCB | 45,0 | 61,6 | 53,3 | igual | 0 |

- Testes: 1477; módulos carregados: 201 (Odoo) e 175 (OCB).
- `l10n_br_sped_base` (fica): 1,71 e 1,37 min no job Odoo, 1,27 e 1,71 no OCB. O OCA/l10n-brazil#5775
  (modelos falsos carregados uma vez por classe de teste) leva os testes dele de 83 a 104 s para 8 s
  no job Odoo, cerca de 1,5 min a menos por job.
- O que os módulos migrados acrescentariam (só referência: CI do `kmee/l10n-brazil-sped` 18.0 no
  runner próprio, que na 16.0 foi 1,8 a 2 vezes mais lento que o hospedado): EFD Contribuições 8,6,
  EFD ICMS/IPI 4,4, apuração 3,2, ECF 1,2, ECD 0,7, DCTFWeb 0,3 (soma 18,4 min; Reinf ainda não
  migrado). Convertendo pela relação medida na 16.0 (casa / hospedado isolado / dentro do l10n-brazil),
  dentro do OCA/l10n-brazil 18.0 seriam cerca de 15 min por job: mesma ordem de grandeza da 16.0.

## Ruído entre rodadas

- Mesmo código, mesmo horário, CI hospedado: o job Odoo da 16.0 com SPED variou de 33,0 a 43,2 min
  (desvio padrão 5,6) e o sem SPED de 31,5 a 41,2 (5,3); o OCB sem SPED de 21,6 a 30,8. Na 18.0 a
  mesma branch variou 13 a 17 min entre as duas rodadas.
- Índice de velocidade da máquina (soma dos segundos de `tests.stats` dos módulos fora do SPED, código
  idêntico nas 6 branches/rodadas da 16.0): de 13,7 a 27,5 min. A máquina sorteada varia até 2 vezes.
- Por isso a diferença bruta das médias (1,8 min no Odoo, 8,3 no OCB) não mede o SPED. Duas medidas
  independentes do ruído concordam: (a) tempo por módulo no log, 0,65 min (Odoo) e 0,57 (OCB);
  (b) duração do job dividida pelo índice da máquina, 1,8% (Odoo) e 1,6% (OCB) a menos sem SPED.
  A concordância também mostra que hoje o SPED não deixa os testes dos outros módulos mais lentos.

## Metodologia

1. Branches no fork `kmee/l10n-brazil`, a partir da mesma cabeça do `origin/<série>`:
   `16.0-medir-base` (base do PR, igual ao origin), `16.0-medir-com-sped` (commit vazio),
   `16.0-medir-sem-sped` (remove os 3 módulos, os `setup/`, as linhas do metapackage e do README);
   `18.0-medir-base` e `18.0-medir-com-sped` (commit vazio). A `16.0-fila-base` não foi usada porque
   não estava na cabeça do origin/16.0.
2. PRs internos em draft no fork, contra as bases acima, disparando o workflow `tests` (mesmo da OCA).
   Reexecuções pelo `gh run rerun`, sempre o par junto.
3. Dos logs brutos da API (`gh api repos/kmee/l10n-brazil/actions/jobs/<id>/logs`): duração do job e
   das etapas (API de jobs), linha `N modules loaded in` do `oca_run_tests` (carga com testes
   at_install), `post-tests in`, `tests.result` e `tests.stats`, e o tempo por módulo (intervalo entre `Loading module X` / início dos testes de X e o evento seguinte;
   inclui instalação e testes do módulo).
4. Acréscimo dos PRs: tempo por módulo no log do head atual de cada PR na OCA, menos o tempo atual do
   mesmo módulo. Soma simples, sem efeito cruzado entre módulos (na medição atual o efeito cruzado
   foi desprezível). Os runs do #4931 e #4992 são de setembro e outubro (base menor), mas o tempo do
   módulo deles é pequeno.

## Links

PRs internos de medição (fechados): kmee/l10n-brazil#914 (16.0 com SPED),
kmee/l10n-brazil#915 (16.0 sem SPED), kmee/l10n-brazil#916 (18.0 linha de base).

| Branch | Run | Rodada | test with Odoo | test with OCB |
|---|---|---|---|---|
| 16.0-medir-com-sped | [45080066220](https://github.com/kmee/l10n-brazil/actions/runs/45080066220) | 1 | [43,2](https://github.com/kmee/l10n-brazil/actions/runs/45080066220/job/137385982217) | [34,8](https://github.com/kmee/l10n-brazil/actions/runs/45080066220/job/137385981460) |
| 16.0-medir-com-sped | 45080066220 | 2 | [41,9](https://github.com/kmee/l10n-brazil/actions/runs/45080066220/job/137398645283) | [40,5](https://github.com/kmee/l10n-brazil/actions/runs/45080066220/job/137398645369) |
| 16.0-medir-com-sped | 45080066220 | 3 | [33,0](https://github.com/kmee/l10n-brazil/actions/runs/45080066220/job/137411080031) | [32,8](https://github.com/kmee/l10n-brazil/actions/runs/45080066220/job/137411080019) |
| 16.0-medir-sem-sped | [45080069221](https://github.com/kmee/l10n-brazil/actions/runs/45080069221) | 1 | [41,2](https://github.com/kmee/l10n-brazil/actions/runs/45080069221/job/137385990547) | [30,6](https://github.com/kmee/l10n-brazil/actions/runs/45080069221/job/137385990802) |
| 16.0-medir-sem-sped | 45080069221 | 2 | [31,5](https://github.com/kmee/l10n-brazil/actions/runs/45080069221/job/137398652321) | [21,6](https://github.com/kmee/l10n-brazil/actions/runs/45080069221/job/137398652398) |
| 16.0-medir-sem-sped | 45080069221 | 3 | [40,1](https://github.com/kmee/l10n-brazil/actions/runs/45080069221/job/137411086182) | [30,8](https://github.com/kmee/l10n-brazil/actions/runs/45080069221/job/137411086566) |
| 18.0-medir-com-sped | [45080074263](https://github.com/kmee/l10n-brazil/actions/runs/45080074263) | 1 | [59,7](https://github.com/kmee/l10n-brazil/actions/runs/45080074263/job/137386007394) | [45,0](https://github.com/kmee/l10n-brazil/actions/runs/45080074263/job/137386007741) |
| 18.0-medir-com-sped | 45080074263 | 2 | [46,4](https://github.com/kmee/l10n-brazil/actions/runs/45080074263/job/137403231635) | [61,6](https://github.com/kmee/l10n-brazil/actions/runs/45080074263/job/137403231607) |

Referências do `kmee/l10n-brazil-sped`: 16.0 hospedado
[44974878665](https://github.com/kmee/l10n-brazil-sped/actions/runs/44974878665) e
[44976549149](https://github.com/kmee/l10n-brazil-sped/actions/runs/44976549149); 16.0 runner próprio
[45060320171](https://github.com/kmee/l10n-brazil-sped/actions/runs/45060320171); 18.0 runner próprio
[45062862991](https://github.com/kmee/l10n-brazil-sped/actions/runs/45062862991),
[45062859358](https://github.com/kmee/l10n-brazil-sped/actions/runs/45062859358),
[45062856578](https://github.com/kmee/l10n-brazil-sped/actions/runs/45062856578),
[45062753708](https://github.com/kmee/l10n-brazil-sped/actions/runs/45062753708).
