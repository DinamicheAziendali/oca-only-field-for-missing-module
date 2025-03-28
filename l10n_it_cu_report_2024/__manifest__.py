# Copyright (C) 2024-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).

{
    "name": "ITA - Stampa Certificazione Unica 2024",
    "summary": "Stampa CU 2024 per l'Italia",
    "author": "Dinamiche Aziendali srl",
    "website": "https://github.com/DinamicheAziendali/certificazione-unica",
    "category": "Localization/Italy",
    "version": "18.0.1.0.1",
    "license": "AGPL-3",
    "depends": [
        "l10n_it_cu",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/account_cu_coordinate_data.xml",
        # "wizard/wizard_cu_file_export_2024_view.xml",
    ],
    "installable": True,
}
