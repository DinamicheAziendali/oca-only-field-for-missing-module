# Copyright 2019-TODAY  Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging

from datetime import timedelta

from odoo import api, fields, models
from odoo.osv.expression import AND
from odoo.tools.misc import flatten
from ..tools.utils import raise_for_status

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    aruba_access_token = fields.Char(
        readonly=True,
        string="Ultimo Token di Accesso",
    )

    aruba_access_token_last_update = fields.Datetime(
        readonly=True,
        string="Data Ultimo Aggiornamento Token",
    )

    aruba_automatic_download = fields.Boolean(
        default=True,
        string="Download Automatico",
    )

    aruba_automatic_update = fields.Boolean(
        default=True,
        string="Aggiornamento Automatico",
    )

    aruba_last_download = fields.Datetime(
        default=fields.Datetime.now,
        string="Ultimo Download da Aruba"
    )

    aruba_premium_account = fields.Boolean(
        string="Account Premium"
    )

    auth_endpoint = fields.Char(
        string="Endpoint di Autenticazione",
    )

    endpoint = fields.Char(
        string="Endpoint Base",
    )

    error_reviewer_ids = fields.Many2many(
        'res.users',
        relation='company_aruba_reviewers_rel',
        column1='company_id',
        column2='user_id',
        help="Questi utenti riceveranno mail di segnalazione qualora il"
             " download delle fatture da Aruba dovesse fallire.",
        store=True,
        string="Revisori",
    )

    grant_type = fields.Char(
        default="password",
        string="Tipologia Grant",
    )

    in_invoices_batch_limit = fields.Integer(
        default=25,
        help="Imposta un numero massimo di fatture da scaricare ad ogni"
             " download automatico. Utile per limitare l'uso delle risorse"
             " del server.",
        string="Limite Fatture In Entrata (numero)",
    )

    in_invoices_days_limit = fields.Integer(
        default=30,
        help="Imposta un numero di giorni entro cui ricercare nuove fatture"
             " in ingresso. Utile per limitare l'uso delle risorse"
             " del server.",
        string="Limite Fatture In Entrata (giorni)",
    )

    is_aruba_setup_complete = fields.Boolean(
        compute='compute_is_aruba_setup_complete',
        store=True,
        string="Setup Completo",
    )

    out_invoices_days_limit = fields.Integer(
        default=30,
        help="Imposta un numero di giorni dopo cui non aggiornare fatture"
             " in uscita. Utile per limitare l'uso delle risorse"
             " del server.",
        string="Limite Fatture In Uscita (giorni)",
    )

    password = fields.Char(
        string="Password",
    )

    receiver_country = fields.Char(
        string="Codice Nazione",
    )

    receiver_vat = fields.Char(
        string="P. Iva",
        default='',
        required=True,
    )

    receiver_fiscalcode = fields.Char(
        string="Fiscalcode",
        default='',
        required=True
    )

    username = fields.Char(
        string="Username",
    )

    @api.model
    def get_aruba_download_companies(self):
        companies = self.search(
            [('aruba_automatic_download', '=', True)],
            order='aruba_last_download asc'
        )
        if len(companies) > 1:
            # Sort company in order to shift every company up one step, and put
            # the first company back to bottom
            companies = companies[1:] + companies[0]
        return companies

    @api.depends(
        'aruba_premium_account',
        'auth_endpoint',
        'endpoint',
        'grant_type',
        'password',
        'receiver_country',
        'receiver_vat',
        'receiver_fiscalcode',
        'username',
    )
    def compute_is_aruba_setup_complete(self):
        for company in self:
            company.is_aruba_setup_complete = company.auth_endpoint \
                and company.auth_endpoint.strip() \
                and company.endpoint \
                and company.endpoint.strip() \
                and company.grant_type \
                and company.grant_type.strip() \
                and company.password \
                and company.password.strip() \
                and company.username \
                and company.username.strip() \
                and (not company.aruba_premium_account
                     or (company.receiver_country
                         and company.receiver_country.strip()
                         and company.receiver_vat
                         and company.receiver_vat.strip()
                         and company.receiver_fiscalcode
                         and company.receiver_fiscalcode.strip()
                         ))

    def download_in_invoices_data_from_aruba(self):
        """
        Returns a list of invoices as dictionaries, and an error string if any
        error occurs
        """
        self.ensure_one()
        if not self.is_aruba_setup_complete:
            return [], f"Setup Aruba incompleto per {self.name}"

        if not self.has_valid_aruba_access_token():
            self.set_aruba_access_token()

        # Find every already downloaded invoices' filenames
        fatt_pa_table = self.env['fatturapa.attachment.in']._table
        ir_att_table = self.env['ir.attachment']._table
        self.env.cr.execute(
            f"""
        SELECT attachment.name FROM {ir_att_table} attachment
        WHERE id in (
            SELECT fatt_pa.ir_attachment_id FROM {fatt_pa_table} fatt_pa
        )
        """
        )
        downloaded = flatten(self.env.cr.fetchall() or [])

        # These params are always the same; 'page' param, instead, needs
        # to be updated after each request until the last page is reached,
        # so we'll update it in the dictionary after every 'while' loop.
        # NB: 'size' param is hardcoded: it defines the invoices number
        # returned from each request, so we'll maximize it to minimize
        # requests' number.
        params = {
            'page': 1,
            'size': 100,
            'username': self.username,
        }
        if self.aruba_premium_account:
            params.update({
                'countryReceiver': self.receiver_country,
                'vatcodeReceiver': self.receiver_vat,
            })
            if self.receiver_fiscalcode:
                params.update({
                    'fiscalcodeReceiver': self.receiver_fiscalcode,
                })


        # Set a start date if a day limit is set (and is > 0)
        if self.in_invoices_days_limit > 0:
            today = fields.Date.today()
            days_limit = self.in_invoices_days_limit
            oldest_date = today - timedelta(days=days_limit)
            params.update({
                'startDate': oldest_date.isoformat()  # ISO 8601
            })

        req_kw = dict(
            method='get',
            general_endpoint=self.endpoint,
            specific_endpoint='/services/invoice/in/findByUsername',
            headers={'Authorization': f'Bearer {self.aruba_access_token}'},
            params=params
        )

        batch = self.in_invoices_batch_limit
        invoices = []

        while True:
            if not self.has_valid_aruba_access_token():
                self.set_aruba_access_token()
                req_kw['headers'] = {
                    'Authorization': f'Bearer {self.aruba_access_token}'
                }

            response = self.env['aruba.sla.request.limit'].request(**req_kw)

            if not (response and response.text):
                return (
                    invoices,
                    f"Company {self.display_name}\n"
                    f"Impossibile trovare fatture all'endpoint Aruba"
                    f" /services/invoice/in/findByUsername; altre fatture"
                    f" potrebbero richiedere un intervento manuale."
                )

            http_error_msg = raise_for_status(response, self)
            if http_error_msg:
                return (
                    invoices,
                    f"Company {self.display_name}\n"
                    f"Impossibile trovare fatture da Aruba per l'errore"
                    f" '{http_error_msg}'; altre fatture"
                    f" potrebbero richiedere un intervento manuale."
                )

            response_json = response.json()
            if response_json.get('errorCode') != '0000':
                code = response_json.get('errorCode')
                descr = response_json.get('errorDescription')
                return (
                    invoices,
                    f"Company {self.display_name}\n"
                    f"Impossibile trovare fatture da Aruba per l'errore"
                    f" '{code}' (``{descr}``); altre fatture"
                    f" potrebbero richiedere un intervento manuale."
                )

            invoices.extend([
                inv
                for inv in (response_json.get('content') or [])
                if inv.get('filename').strip() not in downloaded
            ])

            # NON-ERROR EXIT CONDITIONS
            # Enough invoices to match the batch limit
            if len(invoices) >= batch > 0:
                return invoices[:batch], ""

            # Last page reached
            elif response_json.get('last', False):
                return invoices, ""

            # If neither of the exit condition are met, skip to next page
            req_kw['params']['page'] += 1

    def get_fatt_att_outs_to_update(self):
        self.ensure_one()
        domain = self.get_fatt_att_outs_to_update_domain()
        return self.env['fatturapa.attachment.out'].search(domain)

    def get_fatt_att_outs_to_update_domain(self):
        self.ensure_one()
        to_str = fields.Datetime.to_string
        today = fields.Date.today()
        non_delivered_limit = to_str(today - timedelta(days=10))
        conditions = [
            # Company condition
            [('company_id', '=', self.id)],
            # Non-empty name condition
            ['|',
             ('aruba_filename', '!=', ''),
             ('name', '!=', '')],
            # States conditions
            ['|',
             ('aruba_state', 'in', ('presa_in_carico', 'inviata')),
             '|',
             '&',
             ('aruba_state', '=', 'consegnata'),
             ('invoice_partner_id.is_pa', '=', True),
             '&',
             ('aruba_state', '=', 'non_consegnata'),
             '&',
             ('invoice_partner_id.is_pa', '=', True),
             ('aruba_last_response_date', '>=', non_delivered_limit)]
        ]

        if self.out_invoices_days_limit > 0:
            limit = today - timedelta(days=self.out_invoices_days_limit)
            conditions.append(
                # Date condition
                [('aruba_last_response_date', '>=', to_str(limit))]
            )

        return AND(conditions)

    def has_valid_aruba_access_token(self):
        self.ensure_one()
        if not self.aruba_access_token \
                or not self.aruba_access_token_last_update:
            return False

        # Tokens are valid for 30 minutes, we'll make it 25 to be sure
        expiration_dtm = self.aruba_access_token_last_update \
            + timedelta(minutes=25)
        return fields.Datetime.now() < expiration_dtm

    def set_aruba_access_token(self):
        all_data = self.filtered('is_aruba_setup_complete')
        missing_data = self - all_data

        for company in all_data:
            response = self.env['aruba.sla.request.limit'].request(
                method='post',
                general_endpoint=company.auth_endpoint,
                specific_endpoint='/auth/signin',
                data={
                    'username': company.username.strip(),
                    'password': company.password.strip(),
                    'grant_type': company.grant_type.strip()
                }
            )
            response.raise_for_status()

            company = company.sudo()
            company.write({
                'aruba_access_token': response.json()['access_token'],
                'aruba_access_token_last_update': fields.Datetime.now()
            })

        if missing_data:
            _logger.warning(
                "Missing Aruba setup for companies: {}".format(
                    ', '.join(missing_data.mapped('name'))
                )
            )
            missing_data.sudo().write({'aruba_access_token': ''})
