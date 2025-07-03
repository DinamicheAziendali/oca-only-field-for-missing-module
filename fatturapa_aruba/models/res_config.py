# Copyright 2019-TODAY  Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    aruba_automatic_download = fields.Boolean(
        default=True,
        string="Download Automatico",
    )

    aruba_automatic_update = fields.Boolean(
        default=True,
        string="Aggiornamento Automatico",
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
        help="Questi utenti riceveranno mail di segnalazione qualora il"
             " download delle fatture da Aruba dovesse fallire.",
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
        required=True
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
    def default_get(self, fields_list):
        """ Get Aruba data from settings' company """
        default_vals = super().default_get(fields_list)
        company_id = default_vals.get('company_id')
        if company_id:
            company = self.env['res.company'].browse(company_id)
            default_vals.update(self.get_aruba_company_vals(company))
        return default_vals

    def execute(self):
        """ Update company with Aruba data """
        if self.company_id:
            self.company_id.write(self.set_aruba_company_vals())
        return super().execute()

    def get_aruba_company_vals(self, company):
        """
        Gets Aruba data from given company and returns a dict of default
        values for current res.config.settings record
        """
        company.ensure_one()
        return {
            'aruba_automatic_download': company.aruba_automatic_download,
            'aruba_automatic_update': company.aruba_automatic_update,
            'auth_endpoint': company.auth_endpoint,
            'aruba_premium_account': company.aruba_premium_account,
            'endpoint': company.endpoint,
            'error_reviewer_ids': [(6, 0, company.error_reviewer_ids.ids)],
            'grant_type': company.grant_type or 'password',
            'in_invoices_batch_limit': company.in_invoices_batch_limit,
            'in_invoices_days_limit': company.in_invoices_days_limit,
            'out_invoices_days_limit': company.out_invoices_days_limit,
            'password': company.password,
            'receiver_country': company.receiver_country,
            'receiver_vat': company.receiver_vat,
            'receiver_fiscalcode': company.receiver_fiscalcode,
            'username': company.username,
        }

    def set_aruba_company_vals(self):
        """
        Gets Aruba data from current res.config.settings record and returns a
        dict of values for res.company write()
        """
        self.ensure_one()
        return {
            'aruba_automatic_download': self.aruba_automatic_download,
            'aruba_automatic_update': self.aruba_automatic_update,
            'auth_endpoint': self.auth_endpoint,
            'aruba_premium_account': self.aruba_premium_account,
            'endpoint': self.endpoint,
            'error_reviewer_ids': [(6, 0, self.error_reviewer_ids.ids)],
            'grant_type': self.grant_type,
            'in_invoices_batch_limit': self.in_invoices_batch_limit,
            'in_invoices_days_limit': self.in_invoices_days_limit,
            'out_invoices_days_limit': self.out_invoices_days_limit,
            'password': self.password,
            'receiver_country': self.receiver_country,
            'receiver_vat': self.receiver_vat,
            'receiver_fiscalcode': self.receiver_fiscalcode,
            'username': self.username,
        }
