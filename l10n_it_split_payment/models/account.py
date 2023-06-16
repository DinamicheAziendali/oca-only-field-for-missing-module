# Copyright 2015  Davide Corio <davide.corio@abstract.it>
# Copyright 2015-2016  Lorenzo Battistini - Agile Business Group
# Copyright 2016  Alessio Gerace - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    split_payment = fields.Boolean()


class AccountMove(models.Model):
    _inherit = "account.move"

    amount_sp = fields.Float(
        string="Split Payment",
        digits="Account",
        store=True,
        readonly=True,
        compute="_compute_amount",
    )
    split_payment = fields.Boolean(
        string="Is Split Payment", related="fiscal_position_id.split_payment"
    )

    # def _compute_amount(self):
    #     res = super()._compute_amount()
    #     for move in self:
    #         if move.split_payment:
    #             if move.is_purchase_document():
    #                 continue
    #             move.amount_sp = move.amount_tax
    #             # move.amount_tax = 0.0
    #             move.amount_total = move.amount_untaxed
    #         else:
    #             move.amount_sp = 0.0
    #     return res
    #
    # def _build_debit_line(self):
    #     if not self.company_id.sp_account_id:
    #         raise UserError(
    #             _(
    #                 "Please set 'Split Payment Write-off Account' field in"
    #                 " accounting configuration"
    #             )
    #         )
    #     vals = {
    #         "name": _("Split Payment Write Off"),
    #         "partner_id": self.partner_id.id,
    #         "account_id": self.company_id.sp_account_id.id,
    #         "journal_id": self.journal_id.id,
    #         "date": self.invoice_date,
    #         "price_unit": -self.amount_sp,
    #         "amount_currency": self.amount_sp,
    #         "debit": self.amount_sp,
    #         "credit": 0.0,
    #         "display_type": "tax",
    #         "is_split_payment": True,
    #     }
    #     if self.move_type == "out_refund":
    #         vals["amount_currency"] = -self.amount_sp
    #         vals["debit"] = 0.0
    #         vals["credit"] = self.amount_sp
    #     return vals
    #
    # def write(self, vals):
    #     res = super().write(vals)
    #     for move in self:
    #         if move.split_payment and sum(
    #             ml.balance
    #             for ml in move.line_ids
    #             if ml.display_type == "tax" and not ml.is_split_payment
    #         ):
    #             write_off_line_vals = move._build_debit_line()
    #             if any(ml.is_split_payment for ml in move.line_ids):
    #                 line_sp = move.line_ids.filtered(lambda l: l.is_split_payment)
    #                 if (
    #                     float_compare(
    #                         line_sp[0].price_unit,
    #                         write_off_line_vals["price_unit"],
    #                         precision_rounding=move.currency_id.rounding,
    #                     )
    #                     != 0
    #                 ):
    #                     line_sp[0].write(write_off_line_vals)
    #                     move._sync_dynamic_lines(
    #                         container={"records": move, "self": move}
    #                     )
    #             else:
    #                 if move.amount_sp:
    #                     move.line_ids = [(0, 0, write_off_line_vals)]
    #                     move._sync_dynamic_lines(
    #                         container={"records": move, "self": move}
    #                     )
    #     return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    is_split_payment = fields.Boolean()

    # @api.model_create_multi
    # def create(self, vals_list):
    #     lines = super().create(vals_list)
    #     for line in lines:
    #         if (
    #             line.move_id.split_payment
    #             and not line.is_split_payment
    #             and not any(ml.is_split_payment for ml in line.move_id.line_ids)
    #             and line.move_id.amount_sp
    #         ):
    #             write_off_line_vals = line.move_id._build_debit_line()
    #             line.move_id.line_ids = [(0, 0, write_off_line_vals)]
    #             line.move_id._sync_dynamic_lines(
    #                 container={"records": line.move_id, "self": line.move_id}
    #             )
    #     return lines
