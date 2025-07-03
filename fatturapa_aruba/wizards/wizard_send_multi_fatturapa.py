# Copyright 2019-TODAY  Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models, fields


class WizardSendMultiFatturaPA(models.TransientModel):
    _name = 'wizard.send.multi.fatturapa'
    _description = "Send multiple e-invoices to Aruba"

    @api.model
    def get_default_attachment_out_ids(self):
        return self.env['fatturapa.attachment.out'].search(
            [('id', 'in', self._context.get('active_ids') or []),
             ('aruba_state', '=', 'pronta')]
        )

    attachment_out_ids = fields.Many2many(
        'fatturapa.attachment.out',
        default=get_default_attachment_out_ids,
        domain=[('aruba_state', '=', 'pronta')],
        required=True,
        string="Fatture da Inviare"
    )

    def send(self):
        e_invoice_to_send = self.mapped('attachment_out_ids').filtered(
            lambda r: r.aruba_state == 'pronta')
        company = self.env.user.company_id
        method = 'post'
        general_endpoint = company.endpoint
        specific_endpoint ='/services/invoice/upload'
        domain = [('endpoint', '=', '/services/invoice/upload')]
        limit = self.env['aruba.sla.request.limit'].search(domain, limit=1)
        count = 0
        for e_invoice in e_invoice_to_send:
            e_invoice.send_via_aruba()
            count += 1
            if count % 30 == 0:
                limit.request(method, general_endpoint, specific_endpoint)
        return {'type': 'ir.actions.act_window_close'}
