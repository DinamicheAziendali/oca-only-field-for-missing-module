# Copyright (C) 2023-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# @author: Marco Calcagni <mcalcagni@dinamicheaziendali.it>
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).

import base64

from odoo import _, fields, models
from odoo.exceptions import UserError

global_cu_number = 0
global_total_record_b = 0
global_total_record_d = 0
global_total_record_h = 0


class CUFileExport(models.TransientModel):
    """
    Questa classe genera il file per la trasmissione telematica delle CU
    """
    _name = "cu.file.export"
    _description = "CU File Export Wizard"
    _end_line = "\r\n"
    _len_rec = 16

