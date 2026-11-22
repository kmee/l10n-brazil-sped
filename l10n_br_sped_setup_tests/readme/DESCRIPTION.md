Módulo técnico para o CI deste repositório. Não se destina a bancos de
produção.

O CI instala apenas os módulos deste repositório e suas dependências.
Sem um módulo de plano de contas brasileiro, as empresas de demonstração
do `l10n_br_base` não têm plano de contas e qualquer teste que crie uma
fatura nelas falha. Depender do `l10n_br_coa_generic` carrega o plano
brasileiro nas empresas de demonstração, como no CI do OCA/l10n-brazil.
