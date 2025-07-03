# Copyright (C) 2018-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartnerInherit(models.Model):
    _inherit = "res.partner"

    partner_altridatigestionali_ids = fields.One2many(
        "partner.altridatigestionali",
        "partner_id",
        string="Partner AltriDatiGestionali",
    )
