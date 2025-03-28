# Copyright (C) 2023-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# @author: Marco Calcagni <mcalcagni@dinamicheaziendali.it>
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).

import base64
import io
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.pdf import OdooPdfFileReader


class CUFileImportADEProtocol(models.TransientModel):
    """
    Questa classe importa il protocollo ADE
    """

    _name = "cu.file.import.ade.protocol"
    _description = "CU File Import ADE Protocol"

    ade_pdf = fields.Binary(string="ADE PDF")
    file_name = fields.Char()

    @api.model
    def check_ade_protocol(self, text_ade_protocols):
        active_ids = self.env.context.get("active_ids", [])
        statement_ids = self.env["account.cu.statement"].browse(active_ids)
        certification_se_line = fields.first(
            statement_ids.mapped("certification_se_lines_ids").filtered(lambda csl: csl.fiscalcode)
        )
        if not certification_se_line:
            raise UserError(_("Certifications haven't fiscalcode!"))

        index = text_ade_protocols.find(certification_se_line.fiscalcode)
        text_ade_protocol = text_ade_protocols[:index]
        regex_numeri = re.compile(r"\d+")
        ade_protocol, ade_sequence = [
            match.group()
            for match in regex_numeri.finditer(text_ade_protocol)
        ][-2:]

        line_with_protocol = self.env["account.cu.se.partner"].search(
            [("ade_protocol", "=", ade_protocol)],
            limit=1,
        )
        if line_with_protocol:
            raise UserError(
                _(
                    "ADE Protocol is already imported in this statement: %s"
                ) % line_with_protocol.statement_id.name
            )

    @api.model
    def set_ade_protocol(self, text_ade_protocols):
        active_ids = self.env.context.get("active_ids", [])
        statement_ids = self.env["account.cu.statement"].browse(active_ids)
        certification_se_lines_ids = statement_ids.mapped("certification_se_lines_ids")
        certification_se_lines_ids.ade_protocol = ""
        certification_se_lines_ids.ade_sequence = ""
        for se_line in certification_se_lines_ids:
            if not se_line.fiscalcode:
                continue

            index = text_ade_protocols.find(se_line.fiscalcode)
            text_ade_protocol = text_ade_protocols[:index]
            regex_numeri = re.compile(r"\d+")
            ade_protocol, ade_sequence = [
                match.group()
                for match in regex_numeri.finditer(text_ade_protocol)
            ][-2:]
            se_line.ade_protocol = ade_protocol.rjust(17, "0")[:17]
            se_line.ade_sequence = ade_sequence.rjust(6, "0")[:6]

        for statement in statement_ids:
            attachment_values = {
                "name": "ADE PDF",
                "datas": self.ade_pdf,
                "res_model": "account.cu.statement",
                "res_id": statement.id,
                "type": "binary",
            }
            self.env["ir.attachment"].create(attachment_values)

    def action_import_ade_protocol(self):
        all_pdf_text = ""
        pdf_content = base64.b64decode(self.ade_pdf)
        pdf_reader = OdooPdfFileReader(io.BytesIO(pdf_content))
        for page_num in range(pdf_reader.numPages):
            page = pdf_reader.getPage(page_num)
            all_pdf_text += page.extractText()

        text_to_find = "EsitoProtocollo telematicoProgressivocertificazioneCodice fiscale percipiente"
        index_ade_protocol = all_pdf_text.find(text_to_find)
        text_ade_protocols = all_pdf_text[index_ade_protocol + len(text_to_find):]
        self.check_ade_protocol(text_ade_protocols)
        self.set_ade_protocol(text_ade_protocols)
        return True
