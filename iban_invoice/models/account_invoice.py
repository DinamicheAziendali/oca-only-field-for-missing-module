# Copyright 2019 Ilaria Franchini <i.franchini@apuliasoftware.it>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    @api.onchange("partner_id")
    def change_partner_id(self):
        if self.move_type in ["out_invoice", "out_refund"]:
            self.company_id.id
            # ---- Checks if field bank_transfer_account specifics the main bank
            if (
                self.partner_id.bank_transfer_account
                # and self.partner_id.bank_transfer_account.company_id.id
                # == company_invoice
            ):
                self.partner_bank_id = self.partner_id.bank_transfer_account.id
            else:
                # ----Checks if a company bank is set as main bank transfer
                acc_bank = self.env["res.partner.bank"].search(
                    [
                        ("main_bank_transfer_account", "=", True),
                        # ("company_id", "=", company_invoice),
                    ],
                    limit=1,
                )
                if acc_bank:
                    self.partner_bank_id = acc_bank
                else:
                    if self.company_id.partner_id.bank_ids:
                        # bank_company = self.company_id.partner_id.bank_ids.filtered(lambda b: b.company_id.id == company_invoice)
                        bank_company = self.company_id.partner_id.bank_ids
                        self.partner_bank_id = fields.first(bank_company)
