# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian SPED - Test Setup",
    "summary": "Instala no CI o que os testes do SPED esperam do OCA/l10n-brazil "
    "completo",
    "version": "18.0.1.0.0",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/kmee/l10n-brazil-sped",
    "development_status": "Beta",
    "depends": [
        "l10n_br_coa_generic",
        "l10n_br_coa_simple",
        "l10n_br_nfe",
        "l10n_br_stock_account",
    ],
    "installable": True,
}
