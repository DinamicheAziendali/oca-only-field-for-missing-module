# Copyright (C) 2023-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "ITA - Fattura elettronica - Emissione - Codice prodotto cliente",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "category": "Localization/Italy",
    "summary": "Codice prodotto cliente in fatturapa",
    "author": "Giuseppe Borruso," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-italy",
    "license": "AGPL-3",
    "depends": [
        "l10n_it_fatturapa_out",
        "product_supplierinfo_for_customer_invoice",
    ],
    "data": [
        # "data/invoice_it_template.xml",
    ],
    "installable": True,
    "auto_install": True,
}
