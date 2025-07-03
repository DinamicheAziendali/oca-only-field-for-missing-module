# Copyright 2019-TODAY  Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64
import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from ..tools.utils import manage_error, raise_for_status

_logger = logging.getLogger(__name__)

try:
    import iso8601
except ImportError as err:
    _logger.error(err)

try:
    from requests.utils import super_len
except ImportError as err:
    _logger.error(err)


class FatturaPAAttachmentOut(models.Model):
    _inherit = 'fatturapa.attachment.out'

    aruba_filename = fields.Char(
        string="Filename Aruba"
    )

    aruba_last_response_text = fields.Text(
        string="Ultimo Messaggio da Aruba"
    )

    aruba_last_response_date = fields.Datetime(
        string="Ultimo Contatto da Aruba"
    )

    aruba_state = fields.Selection(
        [('pronta', "Pronta"),
         ('presa_in_carico', "Presa in carico"),
         ('errore_elaborazione', "Errore Elaborazione"),
         ('inviata', "Inviata"),
         ('scartata', "Scartata"),
         ('non_consegnata', "Non Consegnata"),
         ('recapito_impossibile', "Recapito Impossibile"),
         ('consegnata', "Consegnata"),
         ('accettata', "Accettata"),
         ('rifiutata', "Rifiutata"),
         ('decorrenza_termini', "Decorrenza Termini")],
        default='pronta',
        string="Stato E-Fattura",
        tracking=True,
    )

    sdi_creation_date = fields.Datetime(
        string="Data Creazione SDI"
    )

    sdi_id_number = fields.Char(
        string="Numero ID SDI"
    )

    def write(self, vals):
        if 'datas' in vals and any(r.aruba_state != 'pronta' for r in self):
            raise ValidationError(
                "Impossibile modificare il file per una fattura inviata."
            )
        return super().write(vals)

    def unlink(self):
        if any(r.aruba_state != 'pronta' for r in self):
            raise ValidationError(
                "Impossibile cancellare una fattura inviata."
            )
        return super().unlink()

    @api.model
    def is_valid_aruba_state(self, state=None):
        return bool(
            state and state in self._fields['aruba_state'].get_values(self.env)
        )

    def reset_aruba_state(self):
        reset = ('errore_elaborazione', 'scartata', 'rifiutata')
        vals = {'aruba_state': 'pronta'}
        self.filtered(lambda a: a.aruba_state in reset).write(vals)

    def send_via_aruba(self):
        for inv in self:
            if len(inv.out_invoice_ids) != 1:
                error_msg = "Impossibile inviare ad Aruba file con più" \
                            " di 1 fattura."
            elif not inv.company_id.is_aruba_setup_complete:
                error_msg = f"Setup incompleto per {inv.company_id.name}: si" \
                            f" prega completare il setup prima di inviare" \
                            f" alcuna fattura."
            else:
                error_msg = inv.upload_invoice()
                if not error_msg:
                    inv.sending_date = fields.Datetime.now()
            if error_msg:
                inv.write({
                    'aruba_last_response_text': error_msg,
                    'aruba_last_response_date': fields.Datetime.now()
                })
                manage_error(inv, error_msg)

    def upload_invoice(self):
        self.ensure_one()
        company = self.company_id
        if not company.has_valid_aruba_access_token():
            company.set_aruba_access_token()

        response = self.env['aruba.sla.request.limit'].request(
            method='post',
            general_endpoint=company.endpoint,
            specific_endpoint='/services/invoice/upload',
            json={'dataFile': base64.b64decode(self.datas).decode('utf-8')},
            headers={
                'Authorization': f'Bearer {company.aruba_access_token}',
                'Content-Length': str(super_len(self.datas))
            },
        )

        if not (response and response.text):
            null_error_msg = f"{self.name} caricamento fallito: il server" \
                             f" Aruba non ha risposto."
            self.write({
                'aruba_last_response_text': null_error_msg,
                'aruba_last_response_date': fields.Datetime.now()
            })
            return null_error_msg

        http_error_msg = raise_for_status(response, self)
        if http_error_msg:
            self.write({
                'aruba_last_response_text': http_error_msg,
                'aruba_last_response_date': fields.Datetime.now()
            })
            return http_error_msg

        error_msg = ""
        response_json = response.json()
        code = response_json.get('errorCode', 'n.a.')
        if code != '0000':
            desc = response_json.get('errorDescription', 'n.a.')
            error_msg = f"{self.name} caricamento fallito:" \
                        f" codice '{code}', errore '{desc}'"
            self.write({
                'aruba_last_response_text': error_msg,
                'aruba_last_response_date': fields.Datetime.now()
            })
        else:
            self.write({
                'aruba_filename': response_json.get('uploadFileName', 'n.a.'),
                'aruba_last_response_text': "File caricato",
                'aruba_last_response_date': fields.Datetime.now(),
                'aruba_state': 'presa_in_carico',
            })
        return error_msg

    @api.model
    def cron_update_invoices_aruba_state(self):
        start = fields.Datetime.now()
        _logger.info(
            f"\nCron: updating invoices' Aruba states."
            f"\nStarted at: {start}."
        )

        cfg_param_model = self.env['ir.config_parameter']
        n = int(cfg_param_model.get_param('aruba_limit_out_check'))
        all_fpa = self.get_fatt_att_outs_to_update()
        if n:
            n_check = all_fpa[:n]
        else:
            n_check = all_fpa

        for att_out in n_check:
            if not att_out.company_id.has_valid_aruba_access_token():
                att_out.company_id.set_aruba_access_token()
            att_out.update_invoice_aruba_state()

        _logger.info(
            f"\nCron: updating invoices' Aruba states."
            f"\nStarted at: {start}."
            f"\nEnded at: {fields.Datetime.now()}"
        )

    @api.model
    def get_fatt_att_outs_to_update(self):
        fatt_att_out_ids = []
        for company in self.env['res.company'].sudo().search(
            [('aruba_automatic_update', '=', True)]
        ):
            fatt_att_out_ids.extend(company.get_fatt_att_outs_to_update().ids)
        return self.browse(tuple(set(fatt_att_out_ids)))

    def update_invoice_aruba_state(self):
        self.ensure_one()
        company = self.company_id
        if not company.is_aruba_setup_complete:
            incomplete_msg = f"{self.name} aggiornamento fallito:" \
                             f" configurazione incompleta per la company" \
                             f" {company.name}, impossibile connettersi" \
                             f" ad Aruba."
            self.write({
                'aruba_last_response_text': incomplete_msg,
                'aruba_last_response_date': fields.Datetime.now()
            })
            return incomplete_msg

        fname_errors = []
        response = None
        req_kw = dict(
            method='get',
            general_endpoint=company.endpoint,
            specific_endpoint='/services/invoice/out/getByFilename',
            headers={'Authorization': f'Bearer {company.aruba_access_token}'}
        )

        def _res_check(r, f, e=''):
            try:
                res_json = r.json()
            except Exception as err:
                fname_errors.append(
                    f"Filename {f + e}: {repr(err) or str(err)}"
                )
            else:
                err_code = res_json.get('errorCode')
                err_desc = res_json.get('errorDescription')
                if err_code == '0000':
                    return r
                else:
                    fname_errors.append(
                        f"Filename {f + e}: {err_desc} ({err_code})"
                    )
            return None

        # For some unknown reason, Aruba might mismatch filenames, therefore
        # we'll try different ones while retrieving our invoices

        # 1) use Aruba filename
        if self.aruba_filename:
            _logger.info(
                f"Trying to retrieve e-invoice via Aruba filename:"
                f" {self.aruba_filename}"
            )
            req_kw['params'] = {'filename': self.aruba_filename}
            res = self.env['aruba.sla.request.limit'].request(**req_kw)
            response = _res_check(res, self.aruba_filename)

        # 2) use Odoo filename
        if not response and self.name and self.name != self.aruba_filename:
            _logger.info(
                f"Trying to retrieve e-invoice via Odoo filename:"
                f" {self.name}"
            )
            req_kw['params'] = {'filename': self.name}
            res = self.env['aruba.sla.request.limit'].request(**req_kw)
            response = _res_check(res, self.name)

        # 3) try to retrieve invoice by applying any possible combination
        # of Aruba/Odoo filenames and extensions
        if not response:
            filenames = {
                self.aruba_filename.replace('.xml', '').replace('.p7m', ''),
                self.name.replace('.xml', '').replace('.p7m', ''),
            }
            exts = ('', '.xml', '.p7m', '.xml.p7m')
            couples = [(f, e) for f in filenames for e in exts]
            while couples and not response:
                filename, ext = couples.pop(0)
                if filename + ext in (self.name, self.aruba_filename):
                    continue
                _logger.info(
                    f"Trying to retrieve e-invoice via filename:"
                    f" {filename + ext}"
                )
                req_kw['params'] = {'filename': ''.join([filename, ext])}
                res = self.env['aruba.sla.request.limit'].request(**req_kw)
                response = _res_check(res, filename, ext)

        if not (response and response.text):
            null_error_msg = f"{self.name} aggiornamento fallito: nessun" \
                             f" dato restituito dai server Aruba.\n"
            if fname_errors:
                null_error_msg += "Impossibile ritrovare file coi seguenti" \
                                  " nomi:\n{}".format('\n'.join(fname_errors))
            self.write({
                'aruba_last_response_text': null_error_msg,
                'aruba_last_response_date': fields.Datetime.now()
            })
            return null_error_msg

        http_error_msg = raise_for_status(response, self)
        if http_error_msg:
            self.write({
                'aruba_last_response_text': http_error_msg,
                'aruba_last_response_date': fields.Datetime.now()
            })
            return http_error_msg

        error_msg = ""
        invoices = response.json().get('invoices', [{}])
        sdi_date = response.json().get('creationDate', '').strip()
        sdi_num = ''
        sdi_num_error_data = []
        if response.json().get('idSdi'):
            sdi_num = response.json().get('idSdi').strip()
        else:
            sdi_num_error_data.append(
                (self.invoice_partner_id.name,
                 self.aruba_filename or self.name)
            )
        if not (invoices
                and len(invoices) == 1
                and isinstance(invoices, list)
                and isinstance(invoices[0], dict)):
            error_msg = f"File '{self.name}': impossibile aggiornare lo"\
                        f" stato, i server Aruba hanno inviato dati" \
                        f" inconsistenti."
            self.write({
                'aruba_last_response_text': error_msg,
                'aruba_last_response_date': fields.Datetime.now()
            })
            manage_error(self, error_msg)
        else:
            aruba_state = invoices[0].get('status', '').strip().lower()\
                .replace(' ', '_')
            if not self.is_valid_aruba_state(aruba_state):
                error_msg = f"File '{self.name}': impossibile aggiornare lo"\
                            f" stato, i server Aruba hanno segnalano uno" \
                            f" stato sconosciuto."
                self.write({
                    'aruba_last_response_text': error_msg,
                    'aruba_last_response_date': fields.Datetime.now()
                })
                manage_error(self, error_msg)
            elif self.aruba_state != aruba_state:
                try:
                    sdi_date = fields.Datetime.to_string(
                        iso8601.parse_date(sdi_date)
                    )
                except iso8601.ParseError:
                    sdi_date = False
                self.write({
                    'aruba_last_response_text': error_msg,
                    'aruba_last_response_date': fields.Datetime.now(),
                    'aruba_state': aruba_state,
                    'sdi_creation_date': sdi_date,
                    'sdi_id_number': sdi_num,
                })
        if sdi_num_error_data:
            reviewers = company.error_reviewer_ids
            if not reviewers:
                reviewers = self.env.ref('base.user_root')
            email_to = ", ".join(
                [r.email for r in reviewers if r.email])
            inv_error_data = ', '.join(
                f"{inv_name} (partner: {inv_partner})"
                for inv_partner, inv_name in sdi_num_error_data
            )
            ctx = dict(
                self._context, inv_datas=inv_error_data
            )
            template = self.env.ref(
                'fatturapa_aruba'
                '.fatturapa_out_aruba_cron_error_mail_template'
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
        return error_msg
