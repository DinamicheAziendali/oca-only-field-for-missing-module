# Copyright 2019-TODAY  Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging

from datetime import datetime
from lxml import etree
from pytz import timezone as tz, all_timezones as all_tzs

from odoo import models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


def fmt_date(dt, env=None):
    """
    Formats date `dt` while adding timezone info from given `env` (if any).

    :param dt: datetime.datetime obj
    :param env: Odoo Environment obj
    :return: dt as formatted string
    """
    if env and env.context.get('tz'):
        user_tz = env.context.get('tz')
        if user_tz in all_tzs:
            old_tz = tz('UTC' if dt.tzinfo is None else dt.tzinfo)
            new_tz = tz(user_tz)
            dt = old_tz.localize(dt).astimezone(new_tz)
        else:
            _logger.info("Unknown timezone {}".format(user_tz))

    return datetime.strftime(dt, '%d/%m/%Y %H:%M:%S')


def inv_data_2_text_dict(inv, env=None):
    """
    Reads data from `inv` dict in given `env` (if any)

    :param inv: dict {e-invoice field: value}
    :param env: Odoo Environment obj
    :return: dict {title: msg}
    """
    text_dict = {}
    if inv.get('name'):
        text_dict["File: "] = inv['name']
    if inv.get('sdi_creation_date'):
        sdi_date = fmt_date(inv['sdi_creation_date'], env)
        text_dict["Data Creazione SDI: "] = sdi_date
    if inv.get('sdi_id_number'):
        text_dict[f"Numero ID SDI: "] = inv['sdi_id_number']
    if inv.get('aruba_filename'):
        text_dict[f"Aruba Filename: "] = inv['aruba_filename']
    return text_dict


def parse_fattura_ordinaria(doc, invs_data, env=None):
    """
    Parse `doc` according to AssoSoftware styling, adding data from `invs_data`
    :param doc: HTML element
    :param invs_data: list of {invoice field: value} dicts
    :param env: Odoo environment
    :return: updated doc
    """
    # Method `xpath()` returns a list of matching nodes
    for body in doc.xpath('//body'):
        dt_divs = body.xpath("//div[@id='dati-trasmissione']")
        if dt_divs:
            # This `div` is supposed to be unique, so we catch the first one
            dt_div = dt_divs[0]
            uls = dt_div.xpath("//ul")
            if uls:
                # Same as before
                ul = uls[0]
                for inv in invs_data:
                    text_dict = inv_data_2_text_dict(inv, env)
                    for i, (title, msg) in enumerate(text_dict.items()):
                        li = etree.SubElement(ul, 'li')
                        li.text = title
                        span = etree.SubElement(li, 'span')
                        span.text = msg

    return doc


def parse_assosoftware(doc, invs_data, env=None):
    """
    Parse `doc` according to AssoSoftware styling, adding data from `invs_data`
    :param doc: HTML element
    :param invs_data: list of {invoice field: value} dicts
    :param env: Odoo environment
    :return: updated doc
    """
    # Method `xpath()` returns a list of matching nodes
    for body in doc.xpath('//body'):
        fattura_divs = body.xpath(
            "//div[@id='fattura-container']/div[@id='fattura-elettronica']"
        )
        if fattura_divs:
            # This `div` is supposed to be unique, so we catch the first one
            fattura_div = fattura_divs[0]
            div = etree.SubElement(fattura_div, 'div')
            p = etree.SubElement(div, 'p')
            strong = etree.SubElement(p, 'strong')
            strong.text = "Dati di Trasmissione"
            ul = etree.SubElement(div, 'ul')
            for inv in invs_data:
                li = etree.SubElement(ul, 'li')
                text_dict = inv_data_2_text_dict(inv, env)
                for i, (title, msg) in enumerate(text_dict.items()):
                    span = etree.SubElement(li, 'span')
                    span_strong = etree.SubElement(span, 'strong')
                    span_strong.text = title
                    span_span = etree.SubElement(span, 'span')
                    span_span.text = msg
                    if i < len(text_dict) - 1:
                        etree.SubElement(span, 'br')

    return doc


class Attachment(models.Model):
    _inherit = 'ir.attachment'

    def write(self, vals):
        """
        Avoid editing ir.attachment .xml file if an e-invoice linked to it has
        already been sent to Aruba
        """
        if 'datas' in vals:
            if self.env['fatturapa.attachment.out'].search_count(
                [('ir_attachment_id', 'in', self.ids),
                 ('aruba_state', '!=', 'pronta')]
            ):
                raise ValidationError(
                    "Impossibile modificare il file per una fattura inviata."
                )
        return super().write(vals)

    def unlink(self):
        """
        Avoid deleting ir.attachment if an e-invoice linked to it has already
        been sent to Aruba
        """
        if self.env['fatturapa.attachment.out'].search_count(
            [('ir_attachment_id', 'in', self.ids),
             ('aruba_state', '!=', 'pronta')]
        ):
            raise ValidationError(
                "Impossibile cancellare una fattura inviata."
            )
        return super().unlink()

    def get_fattura_elettronica_preview(self):
        preview = super().get_fattura_elettronica_preview()

        # Compatibility check (older l10n_it_fatturapa version without
        # `fatturapa_preview_style` field)
        if not hasattr(self.env['res.company'], 'fatturapa_preview_style'):
            return preview

        domain = [('ir_attachment_id', '=', self.id)]
        in_invs = self.env['fatturapa.attachment.in'].search(domain)
        out_invs = self.env['fatturapa.attachment.out'].search(domain)

        if not (in_invs or out_invs):
            # Nothing to add
            return preview
        # this is needed because some users require sdi creation date and sdi
        # id number
        invs_data = in_invs.read(load='') + out_invs.read(load='')
        if not any([
            i['sdi_creation_date'] or i['sdi_id_number'] for i in invs_data
        ]):
            # Nothing to add
            return preview

        doc = etree.fromstring(preview)
        style = self.env.company.fatturapa_preview_style
        # workaround to support the old and the new version
        # of fatturapa_preview_style
        if style in ('fatturaordinaria_v1.2.1.xsl', 'Foglio_di_stile_fatturaordinaria_v1.2.2.xsl'):
            new_doc = parse_fattura_ordinaria(doc, invs_data, self.env)
        elif style in ('FoglioStileAssoSoftware_v1.1.xsl',
                       'FoglioStileAssoSoftware.xsl'):
            new_doc = parse_assosoftware(doc, invs_data, self.env)
        else:
            raise ValidationError("Stile preview sconosciuto")

        return etree.tostring(new_doc, pretty_print=True)
