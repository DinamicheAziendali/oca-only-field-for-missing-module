# Copyright 2022-TODAY  Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api


class WizardImportFatturapa(models.TransientModel):
    _inherit = "wizard.import.fatturapa"

    #def getPartnerBase(self, DatiAnagrafici, raise_if_duplicated=True):
    def getPartnerBase(self, DatiAnagrafici):
        # actually when we receive the self invoice, there is the problem
        # the invoice contains a vat like FRFR12345678 and is not possibile
        # compute the partner_id, this monkey patch allow avoid block of
        # download cron of Aruba module and we don't need to manage
        # that invoice. The second case of it cover all case is self invoice
        if DatiAnagrafici and hasattr(DatiAnagrafici, "IdFiscaleIVA") and \
                DatiAnagrafici.IdFiscaleIVA and \
                (DatiAnagrafici.IdFiscaleIVA.IdPaese.upper() != "IT" or '99999999999' in DatiAnagrafici.IdFiscaleIVA.IdCodice):
            return False
        else:
            return super().getPartnerBase(
                DatiAnagrafici
                #raise_if_duplicated=raise_if_duplicated
            )
