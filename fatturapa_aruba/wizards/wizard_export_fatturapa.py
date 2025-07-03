# Copyright 2019-TODAY  Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64
from lxml import etree

from odoo import models, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError


class WizardExportFatturaPA(models.TransientModel):
    _inherit = 'wizard.export.fatturapa'

    def exportFatturaPA_1by1(self):
        """
        This method is required to allow each electronic invoice to include
        only 1 invoice, instead of multiple ones
        """
        att_ids = []
        fattpa_out_obj = self.env['fatturapa.attachment.out']
        for invoice_id in self._context.get('active_ids', []):
            act = self.with_context(active_ids=[invoice_id]).exportFatturaPA()
            if act.get('res_id', False):
                att_ids.append(act['res_id'])
            elif act.get('domain', False):
                domain = act['domain']
                if isinstance(domain, str):
                    domain = safe_eval(domain)
                att_ids.extend(fattpa_out_obj.search(domain).ids)

        action = {
            'name': "Export Fatture Elettroniche",
            'res_model': 'fatturapa.attachment.out',
            'type': 'ir.actions.act_window',
        }
        if len(att_ids) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = att_ids[0]
        else:
            action['view_mode'] = 'tree,form'
            action['domain'] = [('id', 'in', att_ids)]
        return action

    def saveAttachment(self, fatturapa, number):
        ir_att = super().saveAttachment(fatturapa, number)
        decoded_datas = base64.decodebytes(ir_att.datas)
        doc = etree.XML(decoded_datas)
        sender = fatturapa.company_id.fatturapa_sender_partner
        id_paese = sender.country_id.code
        if not sender.vat:
            raise UserError(
                _('Sender does not have VAT number.')
            )
        if not sender.phone:
            raise UserError(_('Sender Phone not set.'))
        if not sender.email:
            raise UserError(_('Sender Email not set.'))
        id_codice = sender.vat[2:]
        common_node = "DatiTrasmissione/IdTrasmittente"
        for id_paese_node in doc.xpath(f"//{common_node}/IdPaese"):
            id_paese_node.text = id_paese
        for id_codice_node in doc.xpath(f"//{common_node}/IdCodice"):
            id_codice_node.text = id_codice
        contact_node = "DatiTrasmissione/ContattiTrasmittente"
        for phone in doc.xpath(f"//{contact_node}/Telefono"):
            phone.text = sender.phone
        for email in doc.xpath(f"//{contact_node}/Email"):
            email.text = sender.email
        content = etree.tostring(doc, xml_declaration=True, encoding='utf-8')
        ir_att.datas = base64.encodebytes(content)
        return ir_att
