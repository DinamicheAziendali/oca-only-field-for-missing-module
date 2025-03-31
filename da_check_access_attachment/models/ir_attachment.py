# Copyright (C) 2023-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).

from odoo import api, models


class IrAttachmentInherit(models.Model):
    _inherit = "ir.attachment"

    @api.model
    def check(self, mode, values=None):
        if self:
            self.env["ir.attachment"].flush_model(["res_model", "res_id"])
            self._cr.execute(
                "SELECT res_model, res_id FROM ir_attachment WHERE id IN %s",
                [tuple(self.ids)],
            )
            for res_model, res_id in self._cr.fetchall():
                if not (res_model and res_id) or res_model in [
                    "fatturapa.attachment.out",
                    "fatturapa.attachment.in",
                ]:
                    return True
        return super(IrAttachmentInherit, self).check(mode, values)
