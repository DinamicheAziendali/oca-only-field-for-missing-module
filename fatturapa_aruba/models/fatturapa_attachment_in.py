# Copyright 2019-TODAY  Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging

from odoo import api, fields, models
from ..tools.utils import raise_for_status

SELF_INVOICE_TYPES = ("TD16", "TD17", "TD18", "TD19", "TD20", "TD21")

_logger = logging.getLogger(__name__)

try:
    import iso8601
except ImportError as err:
    _logger.error(err)


class FatturaPAAttachmentIn(models.Model):
    _inherit = 'fatturapa.attachment.in'

    sdi_creation_date = fields.Datetime(
        string="Data Creazione SDI"
    )

    sdi_id_number = fields.Char(
        string="Numero ID SDI"
    )

    @api.model
    def cron_download_invoices_via_aruba(self):
        start = fields.Datetime.now()
        _logger.info(
            f"\nCron: downloading invoices from Aruba."
            f"\nStarted at: {start}."
        )

        for company in self.env['res.company'].get_aruba_download_companies():
            html_error = []
            invoices, error = company.download_in_invoices_data_from_aruba()

            if error:
                html_error.append(error)

            inv_total = len(invoices)
            for inv in invoices:
                error_msg = self.create_fatturapa_from_aruba_data(company, inv)
                if error_msg:
                    html_error.append(error_msg)

            if html_error:
                reviewers = company.error_reviewer_ids
                if not reviewers:
                    reviewers = self.env.ref('base.user_root')
                email_to = ", ".join(
                    [r.email for r in reviewers if r.email])

                msg = "<ol><li>" + "</li><li>".join(html_error) + "</li></ol>"

                ctx = dict(
                    self._context, mail_error_msg=msg, inv_total=inv_total
                )
                template = self.env.ref(
                    'fatturapa_aruba'
                    '.fatturapa_in_aruba_cron_error_mail_template'
                )
                template.write({
                    'email_to': email_to,
                    'email_from': self.env.ref('base.user_root').email
                })
                template.with_context(ctx).send_mail(res_id=company.id)
                template.write({
                    'email_to': False,
                    'email_from': False
                })

            company.aruba_last_download = fields.Datetime.now()

        _logger.info(
            f"\nCron: downloading invoices from Aruba."
            f"\nStarted at: {start}."
            f"\nEnded at: {fields.Datetime.now()}"
        )

    def create_fatturapa_from_aruba_data(self, company, data):
        if not company.is_aruba_setup_complete:
            return f"Impossibile scaricare le fatture da Aruba: setup" \
                   f" incompleto per la company {company.name}."

        if not company.has_valid_aruba_access_token():
            company.set_aruba_access_token()

        nan = "\'N.A.\'"
        file_id = data.get('id', '') or nan
        filename = data.get('filename', '').strip() or nan
        sdi_date = data.get('creationDate', '').strip()
        sdi_num = data.get('idSdi', '')
        # Note: in some cases Aruba api provides None as a result for sdi_num
        # and in this case is not possible to do strip()
        if sdi_num is None:
            sdi_num = ''
        else:
            sdi_num = sdi_num.strip()
        sender = data.get('sender', {}).get('description', '').strip() or nan

        if not filename:
            return f"Impossibile recuperare filename per fattura elettronica" \
                   f" da {sender} (ID interno Aruba: {file_id})"

        endpoint = '/services/invoice/in/getByFilename'
        response = self.env['aruba.sla.request.limit'].request(
            method='get',
            general_endpoint=company.endpoint,
            specific_endpoint=endpoint,
            headers={'Authorization': f'Bearer {company.aruba_access_token}'},
            params={'filename': filename}
        )

        if not (response and response.text):
            return f"Nessuna risposta ricevuta dal server Aruba per la" \
                   f" fattura {filename} (endpoint: {endpoint})"

        raise_for_status_msg = raise_for_status(response, company)
        if raise_for_status_msg:
            return f"Nessuna risposta ricevuta dal server Aruba per il file" \
                   f" {filename} (endpoint: {endpoint}). Richiesta fallita" \
                   f" con errore '{raise_for_status_msg}'"

        file = response.json().get('file', '')
        try:
            sdi_date = fields.Datetime.to_string(iso8601.parse_date(sdi_date))
        except iso8601.ParseError:
            sdi_date = False
        try:
            self.create([{
                'company_id': company.id,
                'datas': file,
                'name': filename,
                'sdi_creation_date': sdi_date,
                'sdi_id_number': sdi_num,
            }])
        except BaseException as e:
            return f"Odoo non è riuscito a creare la fattura da {sender}" \
                   f" (ID interno Aruba: {file_id}, file: {filename})." \
                   f" Errore: {str(e)}"

        return

    @api.depends("xml_supplier_id")
    def _compute_registered(self):
        res = super()._compute_registered()
        for att in self:
            if not att.ir_attachment_id.datas:
                continue

            fatt = att.get_invoice_obj()

            for invoice_body in fatt.FatturaElettronicaBody:
                dgd = invoice_body.DatiGenerali.DatiGeneraliDocumento
                # when the self invoice is received, I don't need to manage
                # then I put as registered directly
                if dgd.TipoDocumento in SELF_INVOICE_TYPES:
                    att.registered = True

        return res
