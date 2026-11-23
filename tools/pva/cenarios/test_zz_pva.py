"""Scenarios of the PVA workflow (tools/pva): EFD ICMS/IPI and EFD Contribuicoes.

Copied into the tests of l10n_br_sped_efd_icms_ipi by tools/pva/gerar.sh, in a
throwaway checkout, and never committed in the module. Each class builds its
scenario, closes the assessments and writes the file made by the button of the
declaration in the directory of PVA_SAIDA, named <kind>__<scenario>.txt, with
the chatter of the declaration next to it (.log.html).

- Lucro Presumido: entries for resale (one supplier in RJ, one in SP emitted in
  October and received in November), a cancelled entry, one sale, ICMS, IPI,
  PIS and COFINS assessed; variants with the 0015 (tax substitute in RJ) and
  with a return of purchase (C110, C113, 0450);
- Lucro Real, EFD Contribuicoes of October and November: credit above the
  contribution in October, balance used in November, use and consumption and
  fixed asset in November.
"""

import base64
import calendar
import logging
import os
from datetime import date, datetime

from odoo.tests.common import Form, tagged

from odoo.addons.l10n_br_tax_assessment.tests.common_entrada import SpedEntradaCommon

_logger = logging.getLogger(__name__)

OUT = os.environ.get("PVA_SAIDA", "/tmp/pva_out")

# what changes between the series
VAT = "cnpj_cpf"
IE = "inscr_est"
PAYABLE = "property_tax_payable_account_id"
RECEIVABLE = "property_tax_receivable_account_id"
GROUP_PER_COMPANY = False


def _account_company(company):
    return {"company_id": company.id}


ICMS_HEADER = {
    "COD_VER": "020",
    "CLAS_ESTAB_IND": "00",
    "IND_PERFIL": "A",
    "IND_ATIV": "0",
    "COD_FIN": "0",
    "ind_apur": "0",
    "cod_receita": "046-2",
    "cod_obrigacao": "000",
}


class PvaScenario(SpedEntradaCommon):
    with_0015 = False
    with_return = False
    hold_assessments = False

    @staticmethod
    def _last_day(month):
        return calendar.monthrange(2026, month)[1]

    def _tax_group(self, tax_domain):
        domain = [
            (
                "fiscal_tax_group_id",
                "=",
                self.env.ref(f"l10n_br_fiscal.tax_group_{tax_domain}").id,
            )
        ]
        if GROUP_PER_COMPANY:
            domain.append(("company_id", "=", self.company.id))
        return self.env["account.tax.group"].search(domain, limit=1)

    def _assess(self, tax_domain, month=11):
        if self.hold_assessments:
            return None
        group = self._tax_group(tax_domain)
        self._prepare_group(group, tax_domain)
        if not group.with_company(self.company)[PAYABLE]:
            accounts = {}
            for field, suffix, name, kind in (
                (PAYABLE, "PAY", "a recolher", "liability_current"),
                (RECEIVABLE, "REC", "a recuperar", "asset_current"),
            ):
                accounts[field] = (
                    self.env["account.account"]
                    .create(
                        {
                            "name": f"{tax_domain} {name}",
                            "code": f"{tax_domain.upper()}{suffix}",
                            "account_type": kind,
                            **_account_company(self.company),
                        }
                    )
                    .id
                )
            group.with_company(self.company).write(accounts)
        assessment = self.env["l10n_br_tax.assessment"].create(
            {
                "company_id": self.company.id,
                "tax_group_id": group.id,
                "date_from": date(2026, month, 1),
                "date_to": date(2026, month, self._last_day(month)),
            }
        )
        assessment.action_compute()
        assessment.action_post()
        _logger.info(
            "PVA assessment %s %s %s debit %s credit %s balance %s",
            tax_domain,
            month,
            assessment.regime,
            assessment.debit_total,
            assessment.credit_total,
            assessment.balance,
        )
        return assessment

    def _prepare_group(self, group, tax_domain):
        """Hook: the Lucro Real writes the regime of PIS and COFINS."""

    def _set_dates(self, document, when):
        # raw SQL: the inverse of document_date would move the bill of month
        self.env.cr.execute(
            "UPDATE l10n_br_fiscal_document SET document_date = %s, date_in_out = %s"
            " WHERE id = %s",
            (when, when, document.id),
        )
        document.invalidate_recordset(["document_date", "date_in_out"])

    def _sale(self, number, invoice_date):
        ref = self.env.ref
        bill = self.init_invoice(
            "out_invoice",
            partner=self.partner_a,
            invoice_date=invoice_date,
            products=[self.product_a],
            document_type=ref("l10n_br_fiscal.document_55"),
            fiscal_operation=ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[ref("l10n_br_fiscal.fo_venda_venda")],
            document_serie_id=self.empresa_lc_document_55_serie_1,
        )
        bill.action_post()
        document = bill.fiscal_document_id
        self._set_dates(
            document,
            datetime(invoice_date.year, invoice_date.month, invoice_date.day, 12),
        )
        number = document.document_number or number
        document.write(
            {
                "state_edoc": "autorizada",
                "document_key": self._access_key(str(number), "11222333000181"),
            }
        )
        return bill

    def _purchase_return(self, bill, invoice_date):
        """Own NF-e returning the purchase of the bill (C110, C113, 0450)."""
        ref = self.env.ref
        refund = self.init_invoice(
            "in_refund",
            partner=bill.partner_id,
            invoice_date=invoice_date,
            products=[self.product_a],
            document_type=ref("l10n_br_fiscal.document_55"),
            fiscal_operation=ref("l10n_br_fiscal.fo_devolucao_compras"),
            fiscal_operation_lines=[
                ref("l10n_br_fiscal.fo_devolucao_compras_comercializacao")
            ],
            document_serie_id=self.empresa_lc_document_55_serie_1,
        )
        refund.action_post()
        document = refund.fiscal_document_id
        self._set_dates(
            document,
            datetime(invoice_date.year, invoice_date.month, invoice_date.day, 12),
        )
        number = document.document_number or "802"
        document.write(
            {
                "state_edoc": "autorizada",
                "document_key": self._access_key(str(number), "11222333000181"),
                "customer_additional_data": "Devolucao da NF-e 501 de 05/11/2026",
            }
        )
        self.env["l10n_br_fiscal.document.related"].create(
            {
                "document_id": document.id,
                "document_related_id": bill.fiscal_document_id.id,
                "document_type_id": ref("l10n_br_fiscal.document_55").id,
                "document_key": bill.fiscal_document_id.document_key,
            }
        )
        return refund

    def _bill(
        self, operation_line, number, invoice_date, payment_term=None, partner=None
    ):
        ref = self.env.ref
        partner = partner or self.partner_a
        bill = self.init_invoice(
            "in_invoice",
            partner=partner,
            invoice_date=invoice_date,
            products=[self.product_a],
            document_type=ref("l10n_br_fiscal.document_55"),
            fiscal_operation=ref("l10n_br_fiscal.fo_compras"),
            fiscal_operation_lines=[ref(f"l10n_br_fiscal.{operation_line}")],
            document_serie="1",
            document_number=number,
        )
        if payment_term:
            with Form(bill) as bill_form:
                bill_form.invoice_payment_term_id = ref(f"account.{payment_term}")
        bill.action_post()
        cnpj = "".join(c for c in partner[VAT] if c.isdigit())
        bill.fiscal_document_id.write(
            {
                "state_edoc": "autorizada",
                "document_key": self._access_key(number, cnpj),
                "imported_document": True,
            }
        )
        return bill

    def _scenario(self):
        partner = self.company.partner_id
        sao_paulo = self.env["res.city"].search(
            [("name", "=", "São Paulo"), ("state_id.code", "=", "SP")], limit=1
        )
        partner.write(
            {
                "legal_name": "Empresa Lucro Presumido Ltda",
                VAT: "11.222.333/0001-81",
                IE: "110042490114",
                "street_name": "Avenida Paulista",
                "street_number": "1000",
                "street": "Avenida Paulista, 1000",
                "zip": "01311-000",
                "district": "Bela Vista",
                "city_id": sao_paulo.id,
                "phone": "11999999999",
            }
        )
        # interstate supplier (RJ)
        self.partner_a.write(
            {
                "street_name": "Rua do Fornecedor",
                "street_number": "10",
                "street": "Rua do Fornecedor, 10",
                "city_id": self.env["res.city"]
                .search(
                    [("name", "=", "Rio de Janeiro"), ("state_id.code", "=", "RJ")],
                    limit=1,
                )
                .id,
            }
        )
        # intrastate supplier (SP), CNPJ and IE with valid check digits
        supplier_sp = self.partner_a.copy(
            {
                "name": "Fornecedor Paulista",
                "legal_name": "Fornecedor Paulista Ltda",
                VAT: "61.073.944/0001-83",
                IE: "215087330110",
                "state_id": self.env.ref("base.state_br_sp").id,
                "city_id": sao_paulo.id,
                "zip": "01310-100",
                "district": "Bela Vista",
                "street_name": "Rua Augusta",
                "street_number": "200",
                "street": "Rua Augusta, 200",
                "fiscal_profile_id": self.env.ref(
                    "l10n_br_fiscal.partner_fiscal_profile_cnt"
                ).id,
            }
        )
        accountant = self.env["res.partner"].create(
            {
                "name": "Contador Ficticio de Demonstracao",
                "is_company": False,
                "is_accountant": True,
                VAT: "111.444.777-35",
                "crc_code": "1SP123456/O-0",
                "crc_state_id": self.env.ref("base.state_br_sp").id,
                "zip": "01311-000",
                "street_name": "Avenida Paulista",
                "street_number": "1",
                "district": "Bela Vista",
                "phone": "11999999999",
                "email": "contador@exemplo.com.br",
                "country_id": self.env.ref("base.br").id,
                "state_id": self.env.ref("base.state_br_sp").id,
                "city_id": sao_paulo.id,
                "parent_id": partner.id,
            }
        )
        self.company.accountant_id = accountant
        # tax substitute in RJ: the 0015
        if self.with_0015:
            self.env["state.tax.numbers"].create(
                {
                    "partner_id": partner.id,
                    "state_id": self.env.ref("base.state_br_rj").id,
                    "l10n_br_ie_code": "86817306",
                }
            )
        # intrastate, emitted in October, received in November
        old = self._bill(
            "fo_compras_compras_comercializacao",
            "504",
            date(2026, 11, 3),
            partner=supplier_sp,
        )
        self.env.cr.execute(
            "UPDATE l10n_br_fiscal_document SET document_date = %s WHERE id = %s",
            (datetime(2026, 10, 28, 12, 0), old.fiscal_document_id.id),
        )
        old.fiscal_document_id.invalidate_recordset(["document_date"])
        # interstate, paid in 30 days
        bill_501 = self._bill(
            "fo_compras_compras_comercializacao",
            "501",
            date(2026, 11, 5),
            payment_term="account_payment_term_30days",
        )
        # interstate, with an observation and a 10 position benefit code
        benef = self._bill(
            "fo_compras_compras_comercializacao", "505", date(2026, 11, 10)
        )
        benef.fiscal_document_id.manual_fiscal_additional_data = "Observacao fiscal"
        benef.fiscal_document_id.fiscal_line_ids.partner_icms_tax_benefit_code = (
            "SP90090101"
        )
        self._entry_document(
            document_date=datetime(2026, 11, 12, 12, 0), state_edoc="cancelada"
        )
        self._sale("801", date(2026, 11, 12))
        if self.with_return:
            self._purchase_return(bill_501, date(2026, 11, 15))
        for domain in ("icms", "ipi", "pis", "cofins"):
            self._assess(domain)

    def _generate(self, kind, name, month=11, **extra):
        self.env["l10n_br_sped.mixin"]._flush_registers(kind)
        declaration = self.env[f"l10n_br_sped.{kind}.0000"].create(
            {
                "company_id": self.company.id,
                "DT_INI": date(2026, month, 1),
                "DT_FIN": date(2026, month, self._last_day(month)),
                **extra,
            }
        )
        declaration.button_populate_sped_from_odoo()
        declaration.button_create_sped_files()
        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", declaration._name),
                ("res_id", "=", declaration.id),
            ],
            order="id desc",
            limit=1,
        )
        self.assertTrue(attachment, f"{name}: the button made no file")
        os.makedirs(OUT, exist_ok=True)
        base = os.path.join(OUT, f"{kind}__{name}")
        with open(base + ".txt", "wb") as handle:
            handle.write(base64.b64decode(attachment.datas))
        with open(base + ".log.html", "w") as handle:
            handle.write("\n".join(declaration.message_ids.mapped("body")))
        _logger.info("PVA generated %s (%s)", base, attachment.name)


@tagged("post_install", "-at_install")
class TestPvaIcmsPresumido(PvaScenario):
    scenario_name = "presumido"

    def test_pva(self):
        self._scenario()
        self._generate("efd_icms_ipi", self.scenario_name, **ICMS_HEADER)


@tagged("post_install", "-at_install")
class TestPvaIcmsPresumido0015(TestPvaIcmsPresumido):
    with_0015 = True
    scenario_name = "presumido_0015"


@tagged("post_install", "-at_install")
class TestPvaIcmsPresumidoDevolucao(TestPvaIcmsPresumido):
    with_return = True
    scenario_name = "presumido_devolucao"


@tagged("post_install", "-at_install")
class TestPvaContribPresumido(PvaScenario):
    def test_pva(self):
        self._scenario()
        self._generate("efd_pis_cofins", "presumido")


@tagged("post_install", "-at_install")
class TestPvaContribReal(PvaScenario):
    """Lucro Real with credit in October and November.

    The demo marks the PIS and COFINS groups cumulative, so the regime is
    written on the group, as the tests of the module do.
    """

    profit_calculation = "real"

    def _prepare_group(self, group, tax_domain):
        if tax_domain in ("pis", "cofins"):
            group.regime = "non_cumulative"

    def _scenario(self):
        self.company.stock_valuation_via_stock_price = True
        self.company.tax_assessment_start = date(2026, 10, 1)
        # October: resale and industrialization, credit above the contribution
        self._bill("fo_compras_compras_comercializacao", "301", date(2026, 10, 5))
        self._bill("fo_compras_compras", "302", date(2026, 10, 8))
        self._sale("701", date(2026, 10, 12))
        for domain in ("icms", "ipi", "pis", "cofins"):
            self._assess(domain, month=10)
        # November: industrialization, the presumed scenario, use and
        # consumption and fixed asset
        self._bill("fo_compras_compras", "502", date(2026, 11, 8))
        self.hold_assessments = True
        PvaScenario._scenario(self)
        self.hold_assessments = False
        self._bill("fo_compras_compras_uso_consumo", "503", date(2026, 11, 9))
        self._bill("fo_compras_compras_ativo", "506", date(2026, 11, 11))
        for domain in ("icms", "ipi", "pis", "cofins"):
            self._assess(domain)

    def test_pva(self):
        self._scenario()
        self._generate("efd_pis_cofins", "real_mes10", month=10)
        self._generate("efd_pis_cofins", "real_mes11")
