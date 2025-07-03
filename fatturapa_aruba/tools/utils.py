# Copyright 2019-TODAY  Openforce Srls Unipersonale (www.openforce.it)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging
_logger = logging.getLogger(__name__)


def get_complete_url(endpoint, url):
    endpoint = endpoint.strip()
    url = url.strip()
    if endpoint.endswith('/'):
        endpoint = endpoint[:len(endpoint)-1]
    if url.startswith('/'):
        url = url[1:]
    return f'{endpoint}/{url}'


def manage_error(obj, msg):
    _logger.warning(msg)
    if hasattr(obj, 'message_post'):
        obj.message_post(body=msg)


def raise_for_status(response, obj):

    http_error_msg = ''
    if isinstance(response.reason, bytes):
        reason = response.reason.decode('utf-8', 'ignore')
    else:
        reason = response.reason

    code = response.status_code
    url = response.url

    if 300 <= code < 400:
        http_error_msg = f"{code} URL Error: {reason} for url: {url}"

    elif 400 <= code < 500:
        http_error_msg = f"{code} Client Error: {reason} for url: {url}"

    elif 500 <= code < 600:
        http_error_msg = f"{code} Server Error: {reason} for url: {url}"

    if http_error_msg:
        manage_error(obj, http_error_msg)

    return http_error_msg
