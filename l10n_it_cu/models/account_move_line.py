# Copyright 2022-TODAY Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.tools import float_round


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    cu_payment_subject = fields.Boolean(
        compute="_compute_cu_payment_subject",
        string="Payment subject to CU"
    )

    @api.depends(
        "account_type",
        "matched_credit_ids",
        "matched_credit_ids.credit_move_id",
        "matched_debit_ids",
        "matched_debit_ids.debit_move_id",
        "move_id.partner_id",
        "move_id.partner_id.income_type_id",
        "move_id.partner_id.property_account_position_id",
        "move_id.partner_id.property_account_position_id.withholding_tax_ids",
        "move_id.partner_id.property_account_position_id.income_type_id",
    )
    def _compute_cu_payment_subject(self):
        for line in self:
            line.cu_payment_subject = line._get_cu_payment()

    def _get_cu_payment(self):
        self.ensure_one()
        if (
            self.account_type != "liability_payable"
            and not self.account_id.cu_subject
        ):
            return False
        # Line Subjected to CU
        if self.invoice_line_tax_wt_ids or self.account_id.cu_subject:
            return True
        # Matched lines
        rec_amls = self.matched_credit_ids.mapped("credit_move_id")
        rec_amls |= self.matched_credit_ids.mapped("debit_move_id")
        rec_amls |= self.matched_debit_ids.mapped("debit_move_id")
        rec_amls |= self.matched_debit_ids.mapped("credit_move_id")

        amls_subj_to_wt = rec_amls.filtered(
            lambda aml: aml.move_id.line_ids.invoice_line_tax_wt_ids
        )

        am_subj_to_wt = rec_amls.filtered(
            lambda aml:  aml.move_id.fiscal_position_id.income_type_id or
            aml.move_id.fiscal_position_id.withholding_tax_ids
        )

        partner_subj_to_wt = rec_amls.filtered(
            lambda aml: aml.move_id.partner_id.income_type_id or
            aml.move_id.partner_id.property_account_position_id.withholding_tax_ids or
            aml.move_id.partner_id.property_account_position_id.income_type_id
        )

        return any([
            amls_subj_to_wt,
            am_subj_to_wt,
            partner_subj_to_wt
        ])

    def get_se_certification_vals(self):
        self.ensure_one()
        vals = {}
        ams = self.env["account.move"]
        amls = self.env["account.move.line"]
        wt_move_obj = self.env["withholding.tax.move"]
        amount_dp = self.env["decimal.precision"].precision_get("Account")

        vals.update({
            "partner_id": self.partner_id.id,
        })

        amount_total = 0
        amount_untaxed = 0
        amount_withholding_tax_deposit = 0
        amount_ns_withholding_tax_other = 0

        # Vals from WT Move
        domain = [
            ("payment_line_id", "=", self.id),
            ("withholding_tax_id.wt_types", "=", "ritenuta"),
            ("company_id", "=", self.company_id.id)
        ]
        wt_moves = wt_move_obj.search(domain)
        if wt_moves:
            for wt_move in wt_moves:
                wt_vals = wt_move.get_se_certification_vals(vals)
                amount_untaxed += wt_vals.get("amount_untaxed", 0)
                amount_withholding_tax_deposit += wt_vals.get(
                    "amount_withholding_tax_deposit",
                    0
                )
            # Invoices competence through reconciles
            ams |= self.get_invoices_from_reconcile()

        # Vals from AML
        elif self.account_id.cu_subject:
            acc_vals = self.get_se_certification_vals_account()
            amount_total = acc_vals.get("amount_total")
            amount_untaxed = acc_vals.get("amount_untaxed")
            amount_withholding_tax_deposit = acc_vals.get("amount_withholding_tax_deposit")
            amount_ns_withholding_tax_other = acc_vals.get("amount_ns_withholding_tax_other")
            income_type = acc_vals.get("income_type")
            amls |= self

        # Common values
        income_type = self.get_income_type(wt_moves, ams)
        vals.update({
            "amount_total": float_round(amount_total, amount_dp),
            "amount_untaxed": float_round(amount_untaxed, amount_dp),
            "amount_withholding_tax_deposit": float_round(amount_withholding_tax_deposit, amount_dp),
            "amount_ns_withholding_tax_other": float_round(amount_ns_withholding_tax_other, amount_dp),
            "account_move_ids": ams.ids,
            "account_move_line_ids": amls.ids,
            "income_type_id": income_type.id,
            "income_type_code": income_type.code or ""
        })
        return vals

    def get_se_certification_vals_account(self):
        """
        This method try to get values of Withholding tax and its base
        from line with an account subjected to CU.
        """
        account = self.account_id
        wt, msg_err = self.get_withholding_tax_competence()
        amount_dp = self.env["decimal.precision"].precision_get("Account")

        amount_total = 0
        amount_untaxed = 0
        amount_withholding_tax_deposit = 0
        amount_ns_withholding_tax_other = 0
        if account.cu_subject_balance_sign == "credit":
            amount = float_round(self.credit, amount_dp)
        else:
            amount = float_round(self.debit, amount_dp)

        # Base from tax
        if account.cu_subject_balance_type == "tax":
            amount_withholding_tax_deposit = amount
            if wt:
                amount_untaxed = wt.get_base_from_tax(amount)
                amount_untaxed = float_round(
                    amount_untaxed * wt.base,
                    amount_dp
                )

        # Tax from Base
        else:
            amount_untaxed = amount
            if wt:
                amount_withholding_tax_deposit = float_round(
                    amount * ((wt.tax or 0.0) / 100.0), amount_dp
                )

        # Base untaxed amount
        if wt.base:
            amount_total = float_round(
                amount_untaxed * (1 / wt.base),
                amount_dp
            )
            amount_ns_withholding_tax_other = float_round(
                amount_total - amount_untaxed,
                amount_dp
            )

        # CU subjected w/o WT
        if not wt:
            amount_total = amount_untaxed
            amount_ns_withholding_tax_other = amount_untaxed
            amount_untaxed = 0.0

        vals = {
            "amount_total": amount_total,
            "amount_untaxed": amount_untaxed,
            "amount_withholding_tax_deposit": amount_withholding_tax_deposit,
            "amount_ns_withholding_tax_other": amount_ns_withholding_tax_other
        }
        return vals

    def get_income_type(self, wt_moves, invoices):
        """
        It returns income type using the following priority:
        - 1. Payment reason from WT
        - 2. Income type from invoice's fiscal position
        - 3. Income type from partner
        """
        self.ensure_one()
        partner = self.partner_id
        # Fiscal Position
        if invoices:
            fp = fields.first(invoices.mapped("fiscal_position_id").filtered("income_type_id"))
        else:
            fp = partner.property_account_position_id
        # WitholdingTax
        if wt_moves:
            wt = fields.first(wt_moves.mapped("withholding_tax_id"))
        else:
            wt = fields.first(fp.withholding_tax_ids)
        # Dispatch Income Type
        if wt and wt.payment_reason_id:
            income_type = wt.payment_reason_id
        elif fp and fp.income_type_id:
            income_type = fp.income_type_id
        else:
            income_type = partner.income_type_id
        return income_type

    def get_invoices_from_reconcile(self):
        """
        It will take all AMLS reconciled with payment line,
        filtering only AMS of document subject to CU
        Returns:
            AMS: recorset of account moves
        """
        self.ensure_one()
        ams = self.matched_credit_ids.mapped("debit_move_id.move_id")
        ams |= self.matched_credit_ids.mapped("credit_move_id.move_id")
        ams |= self.matched_debit_ids.mapped("debit_move_id.move_id")
        ams |= self.matched_debit_ids.mapped("credit_move_id.move_id")

        ams = ams.filtered(lambda r: r.move_type == "in_invoice")
        return ams

    def get_withholding_tax_competence(self):
        self.ensure_one()
        wt_obj = self.env["withholding.tax"]
        # Check values in line
        msg_err = ""
        if not self.partner_id:
            msg_err = _("Missing partner in registration move {}".format(
                self.move_id.name
            ))
        elif not self.partner_id.property_account_position_id:
            msg_err = _("Missing fiscalposition in partner {}".format(
                self.partner_id.name
            ))
        elif not self.partner_id.property_account_position_id.withholding_tax_ids:
            msg_err = _('Missing Withholding taxes in fiscalposition of partner {}'.format(
                self.partner_id.name
            ))
        wt = fields.first(self.partner_id.property_account_position_id.withholding_tax_ids)
        if wt and not msg_err:
            return wt, msg_err
        else:
            return wt_obj, msg_err
