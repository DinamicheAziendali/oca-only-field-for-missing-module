# © 2016 Andrea Cometa
# Copyright 2023 Simone Rubino - Aion Tech
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class DistintaReportQweb(models.AbstractModel):

    _name = "report.l10n_it_ricevute_bancarie.distinta_qweb"
    _description = "C/O Slip Report"

    def _get_report_values(self, docids, data=None):
        return {
            "doc_ids": docids,
            "doc_model": "riba.distinta",
            "docs": self.env["riba.distinta"].browse(docids),
            "data": data,
        }
