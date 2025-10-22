# Copyright (C) 2018-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class AccountAnalyticAccountInherit(models.Model):
    _inherit = "account.analytic.account"

    cig = fields.Char("CIG Code", size=15)
    cup = fields.Char("CUP Code", size=15)

    # def write(self, values):
    #     for analytic_account in self:
    #         model_sale_order = self.env["sale.order"]
    #         sale_ids = model_sale_order.search([("analytic_account_id", "=", analytic_account.id)])
    #         if "cig" in values:
    #             sale_ids.cig = values["cig"]
    #         if "cup" in values:
    #             sale_ids.cup = values["cup"]
    #     return super().write(values)
