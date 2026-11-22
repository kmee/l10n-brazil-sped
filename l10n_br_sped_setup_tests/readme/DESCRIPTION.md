Módulo técnico para o CI deste repositório. Não se destina a bancos de
produção.

O CI instala apenas os módulos deste repositório e suas dependências, e
os testes dos módulos do SPED foram escritos no CI do OCA/l10n-brazil, que
instala a localização inteira. Este módulo traz o que eles esperam
encontrar no banco:

- `l10n_br_coa_generic` e `l10n_br_coa_simple`: o plano de contas das
  empresas de demonstração e das empresas que o common de testes do
  `l10n_br_account` cria;
- `l10n_br_stock_account`: a valorização do estoque pelo custo líquido,
  sem a qual os testes de entrada sem direito a crédito são pulados;
- `l10n_br_nfe`: a NF-e de venda dos testes só gera a chave de acesso
  pelo processador da NF-e; sem ele, a confirmação recusa a nota de uma
  empresa sem CNPJ.
