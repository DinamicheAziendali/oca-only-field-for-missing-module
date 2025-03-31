# Copyright 2019 Ilaria Franchini <i.franchini@apuliasoftware.it>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    main_bank_transfer_account = fields.Boolean()
    is_company_bank = fields.Boolean(default=False, store=True
        # compute="_compute_company_partner", default=False, store=True
    )

    # @api.depends("partner_id", "company_id", "company_id.partner_id")
    # def _compute_company_partner(self):
    #     company_ids = self.env["res.company"].search([])
    #     partner_ids = company_ids.mapped("partner_id")
    #     for bank in self:
    #         if bank.partner_id in partner_ids:
    #             bank.is_company_bank = True
