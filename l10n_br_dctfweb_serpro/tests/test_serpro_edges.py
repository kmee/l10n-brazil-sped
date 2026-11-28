# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import json
import os
import stat
from unittest import mock

import requests

from odoo.exceptions import UserError
from odoo.tests import tagged

from ..models.integra_contador import _CertificateFiles
from .common import MOCK_POST, FakeResponse, TestSerproCommon, answer
from .test_integra_contador import CERTIFICATE_PATH, fake_certificate


class FakeCertificate:
    """The two PEM halves the A1 certificate of the company gives."""

    def cert_chave(self):
        return ("CERTIFICATE", "KEY")


class NotJsonResponse(FakeResponse):
    """An answer whose body is not JSON, as a proxy error page is."""

    def json(self):
        raise ValueError("not JSON")


@tagged("post_install", "-at_install")
class TestCertificateFiles(TestSerproCommon):
    """The A1 pair lives on disk only for the length of one request."""

    def test_the_pair_is_written_for_the_owner_and_removed_after(self):
        company_class = type(self.env["res.company"])
        with mock.patch.object(
            company_class, "_get_br_ecertificate", return_value=FakeCertificate()
        ):
            files = self.env["l10n_br_dctfweb.integra.contador"]._certificate_files(
                self.company
            )
            self.assertIsInstance(files, _CertificateFiles)
            with files as (cert_path, key_path):
                with open(cert_path) as cert_file:
                    self.assertEqual(cert_file.read(), "CERTIFICATE")
                with open(key_path) as key_file:
                    self.assertEqual(key_file.read(), "KEY")
                mode = stat.S_IMODE(os.stat(key_path).st_mode)
                self.assertEqual(mode, stat.S_IRUSR | stat.S_IWUSR)
        self.assertFalse(os.path.exists(cert_path))
        self.assertFalse(os.path.exists(key_path))

    def test_the_pair_is_removed_when_the_request_fails(self):
        company_class = type(self.env["res.company"])
        with mock.patch.object(
            company_class, "_get_br_ecertificate", return_value=FakeCertificate()
        ):
            files = _CertificateFiles(self.company)
            with self.assertRaises(RuntimeError):
                with files as (cert_path, key_path):
                    raise RuntimeError("the request failed")
        self.assertFalse(os.path.exists(cert_path))
        self.assertFalse(os.path.exists(key_path))


@tagged("post_install", "-at_install")
class TestTransportEdges(TestSerproCommon):
    """Answers and failures the happy path never meets."""

    def setUp(self):
        super().setUp()
        self.transport = self.env["l10n_br_dctfweb.integra.contador"]
        patcher = mock.patch(CERTIFICATE_PATH, side_effect=fake_certificate)
        self.addCleanup(patcher.stop)
        patcher.start()

    def _production_without_token(self):
        self.company.sudo().write(
            {
                "serpro_environment": "production",
                "serpro_access_token": False,
                "serpro_token_expiration": False,
            }
        )

    def test_a_company_without_environment_is_refused(self):
        self.company.sudo().serpro_environment = False
        with self.assertRaises(UserError):
            self.transport._get_token(self.company)

    def test_a_token_request_timeout_becomes_a_user_error(self):
        self._production_without_token()
        with (
            mock.patch(MOCK_POST, side_effect=requests.exceptions.Timeout),
            self.assertRaises(UserError),
        ):
            self.transport._get_token(self.company)

    def test_a_token_request_failure_becomes_a_user_error(self):
        self._production_without_token()
        with (
            mock.patch(MOCK_POST, side_effect=requests.exceptions.ConnectionError),
            self.assertRaises(UserError),
        ):
            self.transport._get_token(self.company)

    def test_refused_credentials_become_a_user_error(self):
        self._production_without_token()
        with (
            mock.patch(MOCK_POST, return_value=FakeResponse({}, status_code=401)),
            self.assertRaises(UserError),
        ):
            self.transport._get_token(self.company)
        self.assertFalse(self.company.sudo().serpro_access_token)

    def test_an_error_page_that_is_not_json_becomes_a_user_error(self):
        with (
            mock.patch(MOCK_POST, return_value=NotJsonResponse(None, status_code=502)),
            self.assertRaises(UserError),
        ):
            self.transport.call(self.company, "12345678000195", "close_assessment", {})

    def test_a_success_that_is_not_json_is_an_empty_body(self):
        with mock.patch(MOCK_POST, return_value=NotJsonResponse(None)):
            body = self.transport.call(
                self.company, "12345678000195", "close_assessment", {}
            )
        self.assertEqual(body, {"_status_code": 200})

    def test_data_that_is_not_json_stays_as_it_came(self):
        with mock.patch(MOCK_POST, return_value=answer("not json {")):
            body = self.transport.call(
                self.company, "12345678000195", "close_assessment", {}
            )
        self.assertEqual(body["dados"], "not json {")


@tagged("post_install", "-at_install")
class TestServiceEdges(TestSerproCommon):
    """The services the flow tests reach only on the happy path."""

    def setUp(self):
        super().setUp()
        patcher = mock.patch(CERTIFICATE_PATH, side_effect=fake_certificate)
        self.addCleanup(patcher.stop)
        patcher.start()

    def _sent(self, post):
        return json.loads(post.call_args.kwargs["json"]["pedidoDados"]["dados"])

    def test_the_taxpayer_needs_a_cnpj_of_fourteen_digits(self):
        self.company.sudo().vat = False
        with self.assertRaises(UserError):
            self.mit._taxpayer_cnpj()

    def test_the_log_is_named_after_the_service(self):
        with mock.patch(
            MOCK_POST, return_value=answer({"protocoloEncerramento": "abc=="})
        ):
            self.mit.action_serpro_close_mit()
        self.assertEqual(self.mit.transmission_count, 1)
        self.assertEqual(self.mit.transmission_ids.name, "ENCAPURACAO314")

    def test_consulting_the_assessment_sends_the_authority_id(self):
        self.mit.serpro_assessment_id = "9"
        with mock.patch(MOCK_POST, return_value=answer({"idApuracao": 9})) as post:
            self.mit.action_serpro_consult_assessment()
        self.assertEqual(self._sent(post), {"idApuracao": 9})

    def test_listing_the_assessments_sends_the_period(self):
        with mock.patch(MOCK_POST, return_value=answer([])) as post:
            self.mit.action_serpro_list_assessments()
        self.assertEqual(self._sent(post), {"anoApuracao": "2026", "mesApuracao": "07"})

    def test_a_declaration_xml_given_as_a_string_is_attached(self):
        self.mit.state = "transmitted"
        with mock.patch(MOCK_POST, return_value=answer("PHhtbC8+")):
            self.mit.action_serpro_fetch_xml()
        self.assertTrue(self.mit.declaration_xml)

    def test_an_answer_without_declaration_xml_is_reported(self):
        self.mit.state = "transmitted"
        with mock.patch(MOCK_POST, return_value=answer({})):
            action = self.mit.action_serpro_fetch_xml()
        self.assertEqual(action["tag"], "display_notification")
        self.assertFalse(self.mit.declaration_xml)

    def test_the_receipt_of_the_transmission_can_come_in_a_structure(self):
        self.mit.write(
            {
                "state": "closed",
                "immediate_transmission": False,
                "signed_declaration_xml": b"c2lnbmVk",
            }
        )
        with mock.patch(MOCK_POST, return_value=answer({"numeroRecibo": "555"})):
            self.mit.action_serpro_transmit_dctfweb()
        self.assertEqual(self.mit.receipt_number, "555")

    def test_a_receipt_answer_without_structure_keeps_the_number(self):
        self.mit.write({"state": "transmitted", "receipt_number": "777"})
        with mock.patch(MOCK_POST, return_value=answer("not a structure")):
            self.mit.action_serpro_receipt()
        self.assertEqual(self.mit.receipt_number, "777")

    def test_a_full_declaration_without_document_attaches_nothing(self):
        self.mit.state = "transmitted"
        with mock.patch(MOCK_POST, return_value=answer({})):
            self.mit.action_serpro_full_declaration()
        self.assertFalse(self.mit.full_declaration_file)

    def test_a_document_can_come_as_a_plain_string(self):
        pdf_from_answer = self.env["l10n_br_dctfweb.assessment"]._pdf_from_answer
        self.assertEqual(pdf_from_answer({"dados": "cGRm"}), "cGRm")
        self.assertFalse(pdf_from_answer({"dados": ["cGRm"]}))
        self.assertFalse(pdf_from_answer({}))

    def test_the_transmissions_open_filtered_by_the_assessment(self):
        action = self.mit.action_view_transmissions()
        self.assertEqual(action["res_model"], "l10n_br_dctfweb.transmission")
        self.assertEqual(action["domain"], [("assessment_id", "=", self.mit.id)])
