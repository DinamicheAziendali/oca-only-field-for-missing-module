# Copyright 2019-TODAY  Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'FatturaPA Aruba',
    'summary': "Sends and manages FatturaPA via the Aruba APIs",
    'version': '18.0.1.9.0',
    'category': 'Account',
    'website': 'http://www.openforce.it',
    'author': 'Openforce',
    'license': 'LGPL-3',
    'external_dependencies': {
        'python': [
            'iso8601',
            'requests'
        ],
        'bin': [],
    },
    'depends': [
        'account',
        'l10n_it_fatturapa',
        'l10n_it_fatturapa_out',
        'l10n_it_fatturapa_in',
    ],
    'data': [
        # 'security/ir.model.access.csv',
        # 'data/aruba_out_config_parameter.xml',
        # 'data/aruba_sla_request_limit.xml',
        # 'data/cron.xml',
        # 'data/mail_template.xml',
        # 'views/account_move.xml',
        # 'views/aruba_sla_request_limit.xml',
        # 'views/fatturapa_attachment_in.xml',
        # 'views/fatturapa_attachment_out.xml',
        # 'views/res_config.xml',
        # 'wizards/wizard_export_fatturapa.xml',
        # 'wizards/wizard_import_fatturapa_xls.xml',
        # 'wizards/wizard_send_multi_fatturapa.xml',
    ],
    'installable': True
}
