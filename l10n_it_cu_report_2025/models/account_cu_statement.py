# Copyright (C) 2025-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).

import base64
import io
import os.path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from odoo import fields, models


class AccountCuStatementInherit(models.Model):
    _inherit = "account.cu.statement"

    def print_se_certification_2025_template(self):
        """
        Generate PDF for SE Certification
        """
        self.ensure_one()
        pdf_bytes = io.BytesIO()
        width, height = A4
        report = canvas.Canvas(pdf_bytes, pagesize=A4)
        img_h = os.path.join(
            os.path.dirname(__file__), "../static/img/CU_H.png"
        )
        report.drawImage(img_h, 0, 0, width=width, height=height, mask="auto")
        space = 0 * cm
        if self.employer_fiscalcode:
            for char in self.employer_fiscalcode:
                report.drawString(11.75 * cm + space, 25.65 * cm, str(char))
                i = 0.08 * cm
                space += 0.60 * cm - i
        header_cu_coordinate_ids = (
            self.env["account.cu.coordinate"].search(
                [
                    ("statement_type_id", "=", self.statement_type_id.id),
                    ("model_id.model", "=", "account.cu.statement"),
                    ("sheet", "=", "H"),
                ],
            )
        )
        for header_cu_coordinate_id in header_cu_coordinate_ids:
            self.write_filed_on_cu(self, header_cu_coordinate_id, report)
        report.showPage()

        for certification_se_line in self.certification_se_lines_ids:
            img_f = os.path.join(
                os.path.dirname(__file__), "../static/img/CU_F.png"
            )
            report.drawImage(
                img_f, 0, 0, width=width, height=height, mask="auto"
            )
            report.drawString(
                16.70 * cm, 26.90 * cm, str(self.statement_type_id.income_year)
            )
            front_cu_coordinate_ids = (
                self.env["account.cu.coordinate"].search(
                    [
                        ("statement_type_id", "=", self.statement_type_id.id),
                        ("model_id.model", "=", "account.cu.statement"),
                        ("sheet", "=", "F"),
                    ],
                )
            )
            for front_cu_coordinate_id in front_cu_coordinate_ids:
                self.write_filed_on_cu(self, front_cu_coordinate_id, report)

            front_cu_coordinate_ids = (
                self.env["account.cu.coordinate"].search(
                    [
                        (
                            "statement_type_id",
                            "=",
                            certification_se_line.statement_type_id.id,
                        ),
                        ("model_id.model", "=", "account.cu.se.partner"),
                        ("sheet", "=", "F"),
                    ],
                )
            )
            for front_cu_coordinate_id in front_cu_coordinate_ids:
                self.write_filed_on_cu(
                    certification_se_line, front_cu_coordinate_id, report
                )
            report.showPage()

            img_rx = os.path.join(
                os.path.dirname(__file__), "../static/img/CU_RX.png"
            )
            rx_cu_coordinate_ids = (
                self.env["account.cu.coordinate"].search(
                    [
                        (
                            "statement_type_id",
                            "=",
                            certification_se_line.statement_type_id.id,
                        ),
                        ("model_id.model", "=", "account.cu.se.partner.line"),
                        ("sheet", "=", "RX"),
                    ],
                )
            )
            first_page_id = fields.first(certification_se_line.line_ids)
            last_page_id = certification_se_line.line_ids[:-1]
            for line in certification_se_line.line_ids:
                report.drawImage(
                    img_rx, 0, 0, width=width, height=height, mask="auto"
                )
                if certification_se_line.fiscalcode:
                    report.drawString(
                        4.40 * cm,
                        28.50 * cm,
                        certification_se_line.fiscalcode
                    )
                for rx_cu_coordinate_id in rx_cu_coordinate_ids:
                    if (
                        rx_cu_coordinate_id.write_once_on == "F"
                        and line == first_page_id
                    ):
                        self.write_filed_on_cu(
                            line, rx_cu_coordinate_id, report
                        )
                    elif (
                        rx_cu_coordinate_id.write_once_on == "L"
                        and line == last_page_id
                    ):
                        self.write_filed_on_cu(
                            line, rx_cu_coordinate_id, report
                        )
                    elif not rx_cu_coordinate_id.write_once_on:
                        self.write_filed_on_cu(
                            line, rx_cu_coordinate_id, report
                        )
                report.showPage()

        report.save()
        file_base64 = base64.b64encode(pdf_bytes.getvalue())
        self.write({"cu_report": file_base64})

    def button_statement_print(self):
        super().button_statement_print()
        return {
            "type": "ir.actions.act_url",
            "url": (
                "/web/content/?model=account.cu.statement&id="
                + str(self.id)
                + "&filename_field=cu_report_name&field=cu_report&download=true&filename="
                + self.cu_report_name
            ),
            "target": "new",
        }

    def export_se_certification_2025(self):
        """
        Generate Export TXT for SE Certification
        """
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_it_cu_report_2025.action_cu_file_export_2025"
        )
        return action
