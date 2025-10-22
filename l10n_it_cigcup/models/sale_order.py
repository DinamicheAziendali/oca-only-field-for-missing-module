# Copyright (C) 2018-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class SaleOrderInherit(models.Model):
    _inherit = "sale.order"

    cig = fields.Char("CIG Code", size=15)
    cup = fields.Char("CUP Code", size=15)

    # def _create_invoices(self, grouped=False, final=False, date=None):
    #     moves = super()._create_invoices(grouped=False, final=False, date=None)
    #     for move in moves:
    #         for sale in move.invoice_line_ids.mapped("sale_line_ids.order_id"):
    #             values_related_document = {
    #                 "type": "contract",
    #                 "name": sale.name,
    #                 "invoice_id": move.id,
    #                 "date": sale.date_order,
    #                 "code": sale.analytic_account_id.code,
    #                 "cig": sale.cig,
    #                 "cup": sale.cup
    #             }
    #             move.related_documents = [(0, 0, values_related_document)]
    #     return moves
    #
    # @api.model
    # def create(self, values):
    #     sale = super().create(values)
    #     if not sale.cig and sale.analytic_account_id.cig:
    #         sale.cig = sale.analytic_account_id.cig
    #     if not sale.cup and sale.analytic_account_id.cup:
    #         sale.cup = sale.analytic_account_id.cup
    #     return sale
    #
    # def write(self, values):
    #     model_analytic_account = self.env["account.analytic.account"]
    #     if "analytic_account_id" in values and values["analytic_account_id"]:
    #         analytic_account_id = model_analytic_account.browse(values["analytic_account_id"])
    #         if "cig" not in values and not self.cig:
    #             values["cig"] = analytic_account_id.cig
    #         if "cup" not in values and not self.cup:
    #             values["cup"] = analytic_account_id.cup
    #     return super().write(values)
