# Copyright 2023-TODAY Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    cu_code_ns_withholding_tax_other = fields.Char(
        help="Code to assign values not subject to WT. To use\
            for example in 'Valori Bollati' and 'Cassa Previdenziale'.",
        string="Code for Ns Withholding Tax Other"
    )

    cu_subject = fields.Boolean(
        string="CU Subject"
    )

    cu_subject_balance_sign = fields.Selection(
        [
            ("credit", "Amount form Credit column"),
            ("debit", "Amount form Debit column"),
        ],
        default="credit",
        string="Balance Sign"
    )

    cu_subject_balance_type = fields.Selection(
        [
            ("base", "Base"),
            ("tax", "Tax"),
        ],
        help="The balance may represent CU base or CU tax",
        string="Balance Type"
    )

    cu_subject_fiscal_position_ids = fields.Many2many(
        "account.fiscal.position",
        relation="account_cu_statement_account_fiscal_position_rel",
        column1="account_cu_statement_id",
        column2="fiscal_position_id",
        string="Fiscal Positions"
    )

    cu_subject_journal_ids = fields.Many2many(
        "account.journal",
        relation="account_cu_statement_account_journal_rel",
        column1="account_cu_statement_id",
        column2="journal_id",
        string="Journals"
    )
