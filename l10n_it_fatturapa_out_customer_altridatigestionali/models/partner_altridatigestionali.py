# Copyright (C) 2018-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PartnerAltriDatiGestionali(models.Model):
    _name = "partner.altridatigestionali"
    _description = "Partner AltriDatiGestionali"

    partner_id = fields.Many2one("res.partner", string="Partner")
    tipo_dato = fields.Char(string="Tipo Dato")
    riferimento_testo = fields.Char(string="Riferimento Testo", default="line.")

    def _get_riferimento_testo(self, line):
        self.ensure_one()
        try:
            return eval(self.riferimento_testo)
        except:
            return " "
