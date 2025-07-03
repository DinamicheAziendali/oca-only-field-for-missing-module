# Copyright 2019-TODAY  Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    aruba_state = fields.Selection(
        readonly=1,
        related='fatturapa_attachment_out_id.aruba_state',
        store=True,
        string="Stato E-Fattura"
    )
