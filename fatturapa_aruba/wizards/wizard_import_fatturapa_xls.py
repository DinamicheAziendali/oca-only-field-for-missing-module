# Copyright 2019-TODAY  Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import base64
import logging
import xlrd

from os.path import splitext

from odoo import fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class WizardUpdateFatturaPAOutXls(models.TransientModel):
    _name = 'wizard.update.fatturapa.out.xls'
    _description = "Import e-invoices status updates from Aruba xls file"

    file = fields.Binary(
        required=True,
        string="File"
    )

    file_name = fields.Char(
        string="Nome File"
    )

    first_row = fields.Integer(
        help="Inserire un numero affinché il file sia importato solo a partire"
             " da una certa riga in poi.",
        string="Prima Riga",
    )

    header_row = fields.Integer(
        default=1,
        required=True,
        string="Riga con Intestazioni"
    )

    last_row = fields.Integer(
        help="Inserire un numero affinché il file sia importato solo fino"
             " a una certa riga.",
        string="Ultima riga",
    )

    sheet_name = fields.Char(
        default="FattureInviate",
        required=True,
        string="Nome Foglio",
    )

    def import_file(self):
        start = fields.Datetime.now()
        _logger.info(
            f"\nImporting file with Aruba data."
            f"\nStarted at: {start}."
        )
        self.check_before_import()
        data = self.parse_file()
        e_invoices = self.update_fatturapa_attachment_out(data)
        if not e_invoices:
            raise ValidationError("Non è stato importato nulla.")

        _logger.info(
            f"\nImporting file with Aruba data."
            f"\nStarted at: {start}."
            f"\nEnded at: {fields.Datetime.now()}"
        )

        return self.launch_view(e_invoices.ids)

    def check_before_import(self):
        file_ext = ''.join(splitext(self.file_name)[-1].split()).lower()
        if file_ext not in ('.xls', '.xlsx'):
            raise ValidationError(
                "Estensione file sconosciuta. Controllare che sia un file di"
                " tipo .xls o .xlsx."
            )

        if self.header_row < 1:
            raise ValidationError(
                "Il numero della riga con le intestazioni dev'essere un"
                " numero intero maggiore di zero."
            )

        if self.first_row:
            if self.first_row < 0:
                raise ValidationError(
                    "Il numero della prima riga non può essere negativo."
                )
            elif not self.header_row < self.first_row:
                raise ValidationError(
                    "Valori inconsistenti per prima riga ed intestazioni."
                )

        if self.last_row:
            if self.last_row < 0:
                raise ValidationError(
                    "Il numero dell'ultima riga non può essere negativo."
                )
            elif not self.header_row < self.last_row:
                raise ValidationError(
                    "Valori inconsistenti per ultima riga ed intestazioni."
                )

        if self.first_row and self.last_row \
                and not self.first_row <= self.last_row:
            raise ValidationError(
                "Valori inconsistenti per prima ed ultima riga."
            )

    def launch_view(self, inv_ids):
        action = {
            'name': "Import Aggiornamenti Fatture Elettroniche",
            'res_model': 'fatturapa.attachment.out',
            'type': 'ir.actions.act_window',
        }
        if len(inv_ids) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = inv_ids[0]
        else:
            action['view_mode'] = 'tree,form'
            action['domain'] = [('id', 'in', inv_ids)]
        return action

    def parse_file(self):
        try:
            file_to_import = base64.decodebytes(self.file)
            workbook = xlrd.open_workbook(file_contents=file_to_import)
        except xlrd.XLRDError:
            raise ValidationError(
                "File xls(x) non valido. Import bloccato."
            )
        try:
            sheet = workbook.sheet_by_name(self.sheet_name)
        except xlrd.biffh.XLRDError:
            raise ValidationError(
                f"Foglio di lavoro '{self.sheet_name}' non trovato."
                f" Import bloccato."
            )

        header_row, first_row, last_row = self.set_main_rows(sheet)
        header_data = sheet.row_values(header_row)

        if first_row == last_row:
            row_data = sheet.row_values(first_row)
            return [dict(zip(header_data, row_data))]

        return [dict(zip(header_data, sheet.row_values(row_num)))
                for row_num in range(first_row, last_row + 1)]

    def set_main_rows(self, sheet):
        header = self.header_row
        first = self.first_row
        last = self.last_row

        if first and last and first == last:
            return header - 1, first - 1, last - 1

        if not (first and first <= sheet.nrows):
            first = header + 1
        if not (last and last <= sheet.nrows):
            last = sheet.nrows

        return header - 1, first - 1, last - 1

    def update_fatturapa_attachment_out(self, data):
        inv_obj = self.env['account.move']
        e_invs = self.env['fatturapa.attachment.out']

        for inv_dict in data:
            inv_number = inv_dict.get('Numero', '')
            upd_inv = inv_obj.search([('name', '=', inv_number)], limit=1)
            if not upd_inv:
                raise ValidationError(
                    f"Aggiornamento fallito, fattura con numero {inv_number}."
                    f" non trovata"
                )

            inv_state = inv_dict.get('Stato', '').strip().lower()\
                .replace(' ', '_')
            if not e_invs.is_valid_aruba_state(inv_state):
                raise ValidationError(
                    f"Aggiornamento fallito per fattura {inv_number}:"
                    f" stato Aruba `{inv_dict.get('Stato', '')}` sconosciuto."
                )

            e_inv = upd_inv.fatturapa_attachment_out_id
            e_inv.write({'aruba_state': inv_state})
            e_invs |= e_inv

        return e_invs
