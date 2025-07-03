# Copyright 2019-TODAY  Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging
import time

from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..tools.utils import get_complete_url

_logger = logging.getLogger(__name__)

try:
    import requests
except ImportError as err:
    _logger.error(err)


class ArubaSLARequestLimit(models.Model):
    _name = 'aruba.sla.request.limit'
    _description = "Aruba SLA Request Limit"
    _order = 'endpoint asc'
    _rec_name = 'endpoint'
    _last_request = None

    endpoint = fields.Char(
        default='/',
        required=True,
        string="Endpoint"
    )

    interval = fields.Selection(
        [('second', "Per second"),
         ('minute', "Per minute"),
         ('hour', "Per hour")],
        default='minute',
        required=True,
        string="Time Interval"
    )

    value = fields.Integer(
        default=1,
        required=True,
        string="Requests"
    )

    xml_id = fields.Char(
        compute='compute_xml_id',
        string="XML ID"
    )

    def compute_xml_id(self):
        xml_ids = self.get_xml_id()
        for sla_limit in self:
            sla_limit.xml_id = xml_ids.get(sla_limit.id) or ''

    @api.model
    def request(self, method, general_endpoint, specific_endpoint, **kw):
        url = get_complete_url(general_endpoint, specific_endpoint)
        sla_limit = self.search([('endpoint', '=', specific_endpoint)])
        _logger.info("Request to: {}".format(url))
        if sla_limit:
            sla_limit.wait()
        type(self)._last_request = datetime.now()
        return requests.request(method, url, **kw)

    @api.constrains('value')
    def check_value(self):
        if any(sla_limit.value <= 0 for sla_limit in self):
            raise ValidationError(
                _("A request limit value must be a positive integer.")
            )

    def get_frequency(self):
        """ Converts `value` to Hz (1/s) if `interval` is not seconds """
        self.ensure_one()
        if self.interval == 'hour':
            return self.value / 3600
        if self.interval == 'minute':
            return self.value / 60
        return self.value

    def wait(self):
        """ Waits to make any request to be Aruba SLA-compliant """
        for sla_limit in self:
            # `get_frequency` returns the number of allowed operations per
            # second (indeed, it's a frequency); to retrieve the wait time in
            # seconds, we simply need to invert its value
            wait_secs = 1 / sla_limit.get_frequency()
            if not self._last_request:
                time.sleep(wait_secs)
            else:
                end = self._last_request + timedelta(seconds=wait_secs)
                start = datetime.now()
                while datetime.now() < end:
                    # Wait till we reach the limit time
                    time.sleep(0.1)
                wait_secs = (datetime.now() - start).total_seconds()
            _logger.info("Request wait time: {}s".format(wait_secs))
