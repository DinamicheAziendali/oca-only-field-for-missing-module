# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################

import ast
import base64
import datetime
import logging
import psycopg2
import re
import smtplib
import threading

from email.utils import formataddr
from odoo import api, fields, models, SUPERUSER_ID, tools, registry, _
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context, split_every
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):

    _inherit = 'res.company'

    display_cc_recipients = fields.Boolean(
        string="Display Recipients Cc (Partners)", default=True)
    display_bcc_recipients = fields.Boolean(
        string="Display Recipients Bcc (Partners)", default=True)
    display_cc = fields.Boolean(string="Display Cc (Emails)")
    display_bcc = fields.Boolean(string="Display Bcc (Emails)")
    display_reply_to = fields.Boolean(string="Display Reply To")
    default_cc = fields.Char(
        'Default Cc (Emails)', help='Carbon copy message recipients (Emails)')
    default_bcc = fields.Char(
        'Default Bcc (Emails)',
        help='Blind carbon copy message recipients (Emails)')
    default_reply_to = fields.Char('Default Reply To')


class MailComposer(models.TransientModel):
    """ Generic message composition wizard. You may inherit from this wizard
        at model and view levels to provide specific features.

        The behavior of the wizard depends on the composition_mode field:
        - 'comment': post on a record. The wizard is pre-populated via ``get_record_data``
        - 'mass_mail': wizard in mass mailing mode where the mail details can
            contain template placeholders that will be merged with actual data
            before being sent to each recipient.
    """
    _inherit = 'mail.compose.message'

    @api.model
    def get_default_cc_email(self):
        if self.env.user.company_id.display_cc:
            return self.env.user.company_id.default_cc
        return False

    @api.model
    def get_default_bcc_emails(self):
        if self.env.user.company_id.display_bcc:
            return self.env.user.company_id.default_bcc
        return False

    @api.model
    def get_default_reply_to(self):
        if self.env.user.company_id.display_reply_to:
            return self.env.user.company_id.default_reply_to
        return False

    email_bcc = fields.Char(
        'Bcc (Emails)', help='Blind carbon copy message (Emails)',
        default=get_default_bcc_emails)
    email_cc = fields.Char(
        'Cc (Emails)', help='Carbon copy message recipients (Emails)',
        default=get_default_cc_email)
    cc_recipient_ids = fields.Many2many(
        'res.partner', 'mail_compose_message_res_partner_cc_rel',
        'wizard_id', 'partner_id', string='Cc (Partners)')
    bcc_recipient_ids = fields.Many2many(
        'res.partner', 'mail_compose_message_res_partner_bcc_rel',
        'wizard_id', 'partner_id', string='Bcc (Partners)')
    display_cc = fields.Boolean(
        string="Display Cc",
        default=lambda self: self.env.user.company_id.display_cc,)
    display_bcc = fields.Boolean(
        string="Display Bcc",
        default=lambda self: self.env.user.company_id.display_bcc,)
    display_cc_recipients = fields.Boolean(
        string="Display Recipients Cc (Partners)",
        default=lambda self: self.env.user.company_id.display_cc_recipients,)
    display_bcc_recipients = fields.Boolean(
        string="Display Recipients Bcc (Partners)",
        default=lambda self: self.env.user.company_id.display_bcc_recipients)
    display_reply_to = fields.Boolean(
        string="Display Reply To",
        default=lambda self: self.env.user.company_id.display_reply_to,)
    email_to = fields.Text('To', help='Message recipients (emails)')
    reply_to = fields.Char(
        'Reply-To', default=get_default_reply_to,
        help='Reply email address. Setting the reply_to bypasses the automatic thread creation.')

    # def get_mail_values(self, res_ids):
    #     """Generate the values that will be used by send_mail to create mail_messages
    #     or mail_mails. """
    #     self.ensure_one()
    #     results = super(MailComposer, self).get_mail_values(res_ids)
    #     for res_id in res_ids:
    #         # static wizard (mail.message) values
    #         results[res_id].update({
    #             'email_bcc': self.email_bcc,
    #             'email_cc': self.email_cc,
    #             'cc_recipient_ids': self.cc_recipient_ids,
    #             'bcc_recipient_ids': self.bcc_recipient_ids,
    #             'reply_to': self.reply_to,
    #             # 'email_to': self.email_to,
    #         })
    #     if self.email_to:
    #         results['to'] = {
    #             'subject': self.subject,
    #             'body': self.body or '',
    #             'parent_id': self.parent_id and self.parent_id.id,
    #             'attachment_ids': [attach.id for attach in self.attachment_ids],
    #             'author_id': self.author_id.id,
    #             'email_from': self.email_from,
    #             'record_name': self.record_name,
    #             'no_auto_thread': self.no_auto_thread,
    #             'mail_server_id': self.mail_server_id.id,
    #             'mail_activity_type_id': self.mail_activity_type_id.id,
    #             'email_bcc': self.email_bcc,
    #             'email_cc': self.email_cc,
    #             'cc_recipient_ids': self.cc_recipient_ids,
    #             'bcc_recipient_ids': self.bcc_recipient_ids,
    #             'reply_to': self.reply_to,
    #             'email_to': self.email_to,
    #             'body_html': self.body or ''
    #             }
    #     elif not self.email_to and (self.email_cc or self.cc_recipient_ids):
    #         results['cc'] = {
    #             'subject': self.subject,
    #             'body': self.body or '',
    #             'parent_id': self.parent_id and self.parent_id.id,
    #             'attachment_ids': [attach.id for attach in self.attachment_ids],
    #             'author_id': self.author_id.id,
    #             'email_from': self.email_from,
    #             'record_name': self.record_name,
    #             'no_auto_thread': self.no_auto_thread,
    #             'mail_server_id': self.mail_server_id.id,
    #             'mail_activity_type_id': self.mail_activity_type_id.id,
    #             'email_bcc': self.email_bcc,
    #             'email_cc': self.email_cc,
    #             'cc_recipient_ids': self.cc_recipient_ids,
    #             'bcc_recipient_ids': self.bcc_recipient_ids,
    #             'reply_to': self.reply_to,
    #             'email_to': self.email_to,
    #             'body_html': self.body or ''
    #             }
    #     return results
    #
    # def send_mail(self, auto_commit=False):
    #     """ Process the wizard content and proceed with sending the related
    #         email(s), rendering any template patterns on the fly if needed. """
    #     notif_layout = self._context.get('custom_layout')
    #     # Several custom layouts make use of the model description at rendering, e.g. in the
    #     # 'View <document>' button. Some models are used for different business concepts, such as
    #     # 'purchase.order' which is used for a RFQ and and PO. To avoid confusion, we must use a
    #     # different wording depending on the state of the object.
    #     # Therefore, we can set the description in the context from the beginning to avoid falling
    #     # back on the regular display_name retrieved in '_notify_prepare_template_context'.
    #     model_description = self._context.get('model_description')
    #     for wizard in self:
    #         # Duplicate attachments linked to the email.template.
    #         # Indeed, basic mail.compose.message wizard duplicates attachments in mass
    #         # mailing mode. But in 'single post' mode, attachments of an email template
    #         # also have to be duplicated to avoid changing their ownership.
    #         if wizard.attachment_ids and wizard.composition_mode != 'mass_mail' and wizard.template_id:
    #             new_attachment_ids = []
    #             for attachment in wizard.attachment_ids:
    #                 if attachment in wizard.template_id.attachment_ids:
    #                     new_attachment_ids.append(attachment.copy({'res_model': 'mail.compose.message', 'res_id': wizard.id}).id)
    #                 else:
    #                     new_attachment_ids.append(attachment.id)
    #             new_attachment_ids.reverse()
    #             wizard.write({'attachment_ids': [(6, 0, new_attachment_ids)]})
    #
    #         # Mass Mailing
    #         mass_mode = wizard.composition_mode in ('mass_mail', 'mass_post')
    #
    #         ActiveModel = self.env[wizard.model] if wizard.model and hasattr(self.env[wizard.model], 'message_post') else self.env['mail.thread']
    #         ActiveModel = ActiveModel.with_context(notify_followers=wizard.notify_followers)
    #         if wizard.composition_mode == 'mass_post':
    #             # do not send emails directly but use the queue instead
    #             # add context key to avoid subscribing the author
    #             ActiveModel = ActiveModel.with_context(mail_notify_force_send=False, mail_create_nosubscribe=True)
    #         # wizard works in batch mode: [res_id] or active_ids or active_domain
    #         if mass_mode and wizard.use_active_domain and wizard.model:
    #             res_ids = self.env[wizard.model].search(ast.literal_eval(wizard.active_domain)).ids
    #         elif mass_mode and wizard.model and self._context.get('active_ids'):
    #             res_ids = self._context['active_ids']
    #         else:
    #             res_ids = [wizard.res_id]
    #
    #         batch_size = int(self.env['ir.config_parameter'].sudo().get_param('mail.batch_size')) or self._batch_size
    #         sliced_res_ids = [res_ids[i:i + batch_size] for i in range(0, len(res_ids), batch_size)]
    #
    #         if wizard.composition_mode == 'mass_mail' or wizard.is_log or (wizard.composition_mode == 'mass_post' and not wizard.notify):  # log a note: subtype is False
    #             subtype_id = False
    #         elif wizard.subtype_id:
    #             subtype_id = wizard.subtype_id.id
    #         else:
    #             subtype_id = self.env['ir.model.data'].xmlid_to_res_id('mail.mt_comment')
    #
    #         for res_ids in sliced_res_ids:
    #             # mass mail mode: mail are sudo-ed, as when going through get_mail_values
    #             # standard access rights on related records will be checked when browsing them
    #             # to compute mail values. If people have access to the records they have rights
    #             # to create lots of emails in sudo as it is consdiered as a technical model.
    #             batch_mails_sudo = self.env['mail.mail'].sudo()
    #             all_mail_values = wizard.get_mail_values(res_ids)
    #             for res_id, mail_values in all_mail_values.items():
    #                 if wizard.composition_mode == 'mass_mail':
    #                     batch_mails_sudo |= self.env['mail.mail'].sudo().create(mail_values)
    #                 else:
    #                     post_params = dict(
    #                         message_type=wizard.message_type,
    #                         subtype_id=subtype_id,
    #                         email_layout_xmlid=notif_layout,
    #                         add_sign=not bool(wizard.template_id),
    #                         mail_auto_delete=wizard.template_id.auto_delete if wizard.template_id else False,
    #                         model_description=model_description,
    #                         **mail_values)
    #                     if ActiveModel._name == 'mail.thread' and wizard.model:
    #                         post_params['model'] = wizard.model
    #                     if res_id not in ['to', 'cc']:
    #                         ActiveModel.browse(res_id).message_post(**post_params)
    #                     else:
    #                         to_mail = self.env['mail.mail'].sudo().create(mail_values)
    #                         if mail_values.get('cc_recipient_ids'):
    #                             to_mail.cc_recipient_ids = [(6, 0, mail_values.get('cc_recipient_ids').ids)]
    #                             to_mail.res_id = False
    #                             # to_mail.sudo().model = False
    #                         to_mail.send(auto_commit=auto_commit)
    #
    #
    #             if wizard.composition_mode == 'mass_mail':
    #                 batch_mails_sudo.send(auto_commit=auto_commit)


class Message(models.Model):
    """ Messages model: system notification (replacing res.log notifications),
        comments (OpenChatter discussion) and incoming emails. """
    _inherit = 'mail.message'

    email_bcc = fields.Char(
        'Bcc (Emails)',
        help='Blind carbon copy message (Emails)')
    email_cc = fields.Char(
        'Cc (Emails)', help='Carbon copy message recipients (Emails)')
    cc_recipient_ids = fields.Many2many(
        'res.partner', 'mail_message_res_partner_cc_rel',
        'message_id', 'partner_id', string='Cc (Partners)')
    bcc_recipient_ids = fields.Many2many(
        'res.partner', 'mail_message_res_partner_bcc_rel',
        'message_id', 'partner_id', string='Bcc (Partners)')
    email_to = fields.Text('To', help='Message recipients (emails)')

    # def message_format(self):
    #     res = super(Message, self).message_format()
    #     partners_dict = {}
    #     for obj in res:
    #         cc_partners = ''
    #         bcc_partners = ''
    #         cc_partners_list = self.env['res.partner'].browse(
    #             obj.get('cc_recipient_ids', [])).read(['name'])
    #         for item in cc_partners_list:
    #             cc_partners += item.get('name') + ', '
    #         bcc_partners_list = self.env['res.partner'].browse(
    #             obj.get('bcc_recipient_ids', [])).read(['name'])
    #         for item in bcc_partners_list:
    #             bcc_partners += item.get('name') + ', '
    #         obj['cc_partners'] = cc_partners
    #         obj['bcc_partners'] = bcc_partners
    #     return res
    #
    # def _get_message_format_fields(self):
    #     message_values = super(Message, self)._get_message_format_fields()
    #     return message_values + [
    #         'email_cc', 'cc_recipient_ids',
    #         'email_bcc', 'bcc_recipient_ids',
    #     ]


# class Mail(models.Model):
#     _inherit = "mail.mail"
#
#     def _send(self, auto_commit=False, raise_exception=False, smtp_session=None):
#         IrMailServer = self.env['ir.mail_server']
#         IrAttachment = self.env['ir.attachment']
#         for mail_id in self.ids:
#             success_pids = []
#             failure_type = None
#             processing_pid = None
#             mail = None
#             try:
#                 mail = self.browse(mail_id)
#                 if mail.state != 'outgoing':
#                     if mail.state != 'exception' and mail.auto_delete:
#                         mail.sudo().unlink()
#                     continue
#
#                 # remove attachments if user send the link with the access_token
#                 body = mail.body_html or ''
#                 attachments = mail.attachment_ids
#                 for link in re.findall(r'/web/(?:content|image)/([0-9]+)', body):
#                     attachments = attachments - IrAttachment.browse(int(link))
#
#                 # load attachment binary data with a separate read(), as prefetching all
#                 # `datas` (binary field) could bloat the browse cache, triggerring
#                 # soft/hard mem limits with temporary data.
#                 attachments = [(a['name'], base64.b64decode(a['datas']), a['mimetype'])
#                                for a in attachments.sudo().read(['name', 'datas', 'mimetype'])]
#
#                 # specific behavior to customize the send email for notified partners
#                 email_list = []
#                 cc_list = []
#                 bcc_list = []
#                 if mail.email_to:
#                     email_list.append(mail._send_prepare_values())
#                 for partner in mail.recipient_ids:
#                     values = mail._send_prepare_values(partner=partner)
#                     values['partner_id'] = partner
#                     email_list.append(values)
#                 for partner in mail.cc_recipient_ids:
#                     cc_list += mail._send_prepare_values(
#                         partner=partner).get('email_to')
#                 for partner in mail.bcc_recipient_ids:
#                     bcc_list += mail._send_prepare_values(
#                         partner=partner).get('email_to')
#
#                 # headers
#                 headers = {}
#                 ICP = self.env['ir.config_parameter'].sudo()
#                 bounce_alias = ICP.get_param("mail.bounce.alias")
#                 catchall_domain = ICP.get_param("mail.catchall.domain")
#                 if bounce_alias and catchall_domain:
#                     if mail.model and mail.res_id:
#                         headers['Return-Path'] = '%s+%d-%s-%d@%s' % (bounce_alias, mail.id, mail.model, mail.res_id, catchall_domain)
#                     else:
#                         headers['Return-Path'] = '%s+%d@%s' % (bounce_alias, mail.id, catchall_domain)
#                 if mail.headers:
#                     try:
#                         headers.update(ast.literal_eval(mail.headers))
#                     except Exception:
#                         pass
#
#                 # Writing on the mail object may fail (e.g. lock on user) which
#                 # would trigger a rollback *after* actually sending the email.
#                 # To avoid sending twice the same email, provoke the failure earlier
#                 mail.write({
#                     'state': 'exception',
#                     'failure_reason': _('Error without exception. Probably due do sending an email without computed recipients.'),
#                 })
#                 # Update notification in a transient exception state to avoid concurrent
#                 # update in case an email bounces while sending all emails related to current
#                 # mail record.
#                 notifs = self.env['mail.notification'].search([
#                     ('notification_type', '=', 'email'),
#                     ('mail_id', 'in', mail.ids),
#                     ('notification_status', 'not in', ('sent', 'canceled'))
#                 ])
#                 if notifs:
#                     notif_msg = _('Error without exception. Probably due do concurrent access update of notification records. Please see with an administrator.')
#                     notifs.sudo().write({
#                         'notification_status': 'exception',
#                         'failure_type': 'UNKNOWN',
#                         'failure_reason': notif_msg,
#                     })
#                     # `test_mail_bounce_during_send`, force immediate update to obtain the lock.
#                     # see rev. 56596e5240ef920df14d99087451ce6f06ac6d36
#                     notifs.flush(fnames=['notification_status', 'failure_type', 'failure_reason'], records=notifs)
#
#                 # build an RFC2822 email.message.Message object and send it without queuing
#                 res = None
#                 for email in email_list:
#                     if email.get('email_to'):
#                         msg = IrMailServer.build_email(
#                             email_from=mail.email_from,
#                             email_to=email.get('email_to'),
#                             subject=mail.subject,
#                             body=email.get('body'),
#                             body_alternative=email.get('body_alternative'),
#                             email_cc=tools.email_split(mail.email_cc) + cc_list,
#                             email_bcc=tools.email_split(mail.email_bcc) + bcc_list,
#                             reply_to=mail.reply_to,
#                             attachments=attachments,
#                             message_id=mail.message_id,
#                             references=mail.references,
#                             object_id=mail.res_id and ('%s-%s' % (mail.res_id, mail.model)),
#                             subtype='html',
#                             subtype_alternative='plain',
#                             headers=headers)
#                         processing_pid = email.pop("partner_id", None)
#                         try:
#                             res = IrMailServer.send_email(
#                                 msg, mail_server_id=mail.mail_server_id.id, smtp_session=smtp_session)
#                             if processing_pid:
#                                 success_pids.append(processing_pid)
#                             processing_pid = None
#                         except AssertionError as error:
#                             if str(error) == IrMailServer.NO_VALID_RECIPIENT:
#                                 failure_type = "RECIPIENT"
#                                 # No valid recipient found for this particular
#                                 # mail item -> ignore error to avoid blocking
#                                 # delivery to next recipients, if any. If this is
#                                 # the only recipient, the mail will show as failed.
#                                 _logger.info("Ignoring invalid recipients for mail.mail %s: %s",
#                                             mail.message_id, email.get('email_to'))
#                             else:
#                                 raise
#                 if res:  # mail has been sent at least once, no major exception occured
#                     mail.write({'state': 'sent', 'message_id': res, 'failure_reason': False})
#                     _logger.info('Mail with ID %r and Message-Id %r successfully sent', mail.id, mail.message_id)
#                     # /!\ can't use mail.state here, as mail.refresh() will cause an error
#                     # see revid:odo@openerp.com-20120622152536-42b2s28lvdv3odyr in 6.1
#                 mail._postprocess_sent_message(success_pids=success_pids, failure_type=failure_type)
#             except UnicodeEncodeError as exc:
#                 _logger.exception('UnicodeEncodeError on text "%s" while processing mail ID %r.', exc.object, mail.id)
#                 raise MailDeliveryException(_("Mail Delivery Failed"), "Invalid text: %s" % exc.object)
#             except MemoryError:
#                 # prevent catching transient MemoryErrors, bubble up to notify user or abort cron job
#                 # instead of marking the mail as failed
#                 _logger.exception(
#                     'MemoryError while processing mail with ID %r and Msg-Id %r. Consider raising the --limit-memory-hard startup option',
#                     mail.id, mail.message_id)
#                 # mail status will stay on ongoing since transaction will be rollback
#                 raise
#             except (psycopg2.Error, smtplib.SMTPServerDisconnected):
#                 # If an error with the database or SMTP session occurs, chances are that the cursor
#                 # or SMTP session are unusable, causing further errors when trying to save the state.
#                 _logger.exception(
#                     'Exception while processing mail with ID %r and Msg-Id %r.',
#                     mail.id, mail.message_id)
#                 raise
#             except Exception as e:
#                 failure_reason = tools.ustr(e)
#                 _logger.exception('failed sending mail (id: %s) due to %s', mail.id, failure_reason)
#                 mail.write({'state': 'exception', 'failure_reason': failure_reason})
#                 mail._postprocess_sent_message(success_pids=success_pids, failure_reason=failure_reason, failure_type='UNKNOWN')
#                 if raise_exception:
#                     if isinstance(e, (AssertionError, UnicodeEncodeError)):
#                         if isinstance(e, UnicodeEncodeError):
#                             value = "Invalid text: %s" % e.object
#                         else:
#                             # get the args of the original error, wrap into a value and throw a MailDeliveryException
#                             # that is an except_orm, with name and value as arguments
#                             value = '. '.join(e.args)
#                         raise MailDeliveryException(_("Mail Delivery Failed"), value)
#                     raise
#
#             if auto_commit is True:
#                 self._cr.commit()
#         return True


# class Thread(models.AbstractModel):
#
#     _inherit = "mail.thread"
#
#     def _notify_record_by_email(self, message, recipients_data, msg_vals=False,
#                                 model_description=False, mail_auto_delete=True, check_existing=False,
#                                 force_send=True, send_after_commit=True,
#                                 **kwargs):
#         """ Method to send email linked to notified messages.
#
#         :param message: mail.message record to notify;
#         :param recipients_data: see ``_notify_thread``;
#         :param msg_vals: see ``_notify_thread``;
#
#         :param model_description: model description used in email notification process
#           (computed if not given);
#         :param mail_auto_delete: delete notification emails once sent;
#         :param check_existing: check for existing notifications to update based on
#           mailed recipient, otherwise create new notifications;
#
#         :param force_send: send emails directly instead of using queue;
#         :param send_after_commit: if force_send, tells whether to send emails after
#           the transaction has been committed using a post-commit hook;
#         """
#         partners_data = [r for r in recipients_data['partners'] if r['notif'] == 'email']
#         if not partners_data:
#             return True
#
#         model = msg_vals.get('model') if msg_vals else message.model
#         model_name = model_description or (self._fallback_lang().env['ir.model']._get(model).display_name if model else False) # one query for display name
#         recipients_groups_data = self._notify_classify_recipients(partners_data, model_name)
#
#         if not recipients_groups_data:
#             return True
#         force_send = self.env.context.get('mail_notify_force_send', force_send)
#
#         template_values = self._notify_prepare_template_context(message, msg_vals, model_description=model_description) # 10 queries
#
#         email_layout_xmlid = msg_vals.get('email_layout_xmlid') if msg_vals else message.email_layout_xmlid
#         template_xmlid = email_layout_xmlid if email_layout_xmlid else 'mail.message_notification_email'
#         try:
#             base_template = self.env.ref(template_xmlid, raise_if_not_found=True).with_context(lang=template_values['lang']) # 1 query
#         except ValueError:
#             _logger.warning('QWeb template %s not found when sending notification emails. Sending without layouting.' % (template_xmlid))
#             base_template = False
#
#         mail_subject = message.subject or (message.record_name and 'Re: %s' % message.record_name) # in cache, no queries
#         # prepare notification mail values
#         base_mail_values = {
#             'mail_message_id': message.id,
#             'mail_server_id': message.mail_server_id.id, # 2 query, check acces + read, may be useless, Falsy, when will it be used?
#             'auto_delete': mail_auto_delete,
#             # due to ir.rule, user have no right to access parent message if message is not published
#             'references': message.parent_id.sudo().message_id if message.parent_id else False,
#             'subject': mail_subject,
#         }
#         headers = self._notify_email_headers()
#         if headers:
#             base_mail_values['headers'] = headers
#
#         Mail = self.env['mail.mail'].sudo()
#         emails = self.env['mail.mail'].sudo()
#
#         # loop on groups (customer, portal, user,  ... + model specific like group_sale_salesman)
#         notif_create_values = []
#         recipients_max = 50
#         for recipients_group_data in recipients_groups_data:
#             # generate notification email content
#             recipients_ids = recipients_group_data.pop('recipients')
#             render_values = {**template_values, **recipients_group_data}
#             # {company, is_discussion, lang, message, model_description, record, record_name, signature, subtype, tracking_values, website_url}
#             # {actions, button_access, has_button_access, recipients}
#
#             if base_template:
#                 mail_body = base_template._render(render_values, engine='ir.qweb', minimal_qcontext=True)
#             else:
#                 mail_body = message.body
#             mail_body = self.env['mail.render.mixin']._replace_local_links(mail_body)
#
#             # create email
#             for recipients_ids_chunk in split_every(recipients_max, recipients_ids):
#                 recipient_values = self._notify_email_recipient_values(recipients_ids_chunk)
#                 email_to = recipient_values['email_to']
#                 recipient_ids = recipient_values['recipient_ids']
#
#                 create_values = {
#                     'body_html': mail_body,
#                     'subject': mail_subject,
#                     'recipient_ids': [(4, pid) for pid in recipient_ids],
#                     'email_bcc': message.email_bcc, 'email_cc': message.email_cc, 'email_to': message.email_to, 'cc_recipient_ids': message.cc_recipient_ids, 'bcc_recipient_ids': message.bcc_recipient_ids,
#                 }
#                 if email_to:
#                     create_values['email_to'] = email_to
#                 create_values.update(base_mail_values)  # mail_message_id, mail_server_id, auto_delete, references, headers
#                 email = Mail.create(create_values)
#
#                 if email and recipient_ids:
#                     tocreate_recipient_ids = list(recipient_ids)
#                     if check_existing:
#                         existing_notifications = self.env['mail.notification'].sudo().search([
#                             ('mail_message_id', '=', message.id),
#                             ('notification_type', '=', 'email'),
#                             ('res_partner_id', 'in', tocreate_recipient_ids)
#                         ])
#                         if existing_notifications:
#                             tocreate_recipient_ids = [rid for rid in recipient_ids if rid not in existing_notifications.mapped('res_partner_id.id')]
#                             existing_notifications.write({
#                                 'notification_status': 'ready',
#                                 'mail_id': email.id,
#                             })
#                     notif_create_values += [{
#                         'mail_message_id': message.id,
#                         'res_partner_id': recipient_id,
#                         'notification_type': 'email',
#                         'mail_id': email.id,
#                         'is_read': True,  # discard Inbox notification
#                         'notification_status': 'ready',
#                     } for recipient_id in tocreate_recipient_ids]
#                 emails |= email
#
#         if notif_create_values:
#             self.env['mail.notification'].sudo().create(notif_create_values)
#
#         # NOTE:
#         #   1. for more than 50 followers, use the queue system
#         #   2. do not send emails immediately if the registry is not loaded,
#         #      to prevent sending email during a simple update of the database
#         #      using the command-line.
#         test_mode = getattr(threading.currentThread(), 'testing', False)
#         if force_send and len(emails) < recipients_max and (not self.pool._init or test_mode):
#             # unless asked specifically, send emails after the transaction to
#             # avoid side effects due to emails being sent while the transaction fails
#             if not test_mode and send_after_commit:
#                 email_ids = emails.ids
#                 dbname = self.env.cr.dbname
#                 _context = self._context
#
#                 @self.env.cr.postcommit.add
#                 def send_notifications():
#                     db_registry = registry(dbname)
#                     with api.Environment.manage(), db_registry.cursor() as cr:
#                         env = api.Environment(cr, SUPERUSER_ID, _context)
#                         env['mail.mail'].browse(email_ids).send()
#             else:
#                 emails.send()
#
#         return True
#
#     def _message_add_suggested_recipient(self, result, partner=None, email=None, reason=''):
#         """ Called by _message_get_suggested_recipients, to add a suggested
#             recipient in the result dictionary. The form is :
#                 partner_id, partner_name<partner_email> or partner_name, reason """
#         self.ensure_one()
#         if email and not partner:
#             # get partner info from email
#             partner_info = self._message_partner_info_from_emails([email])[0]
#             if partner_info.get('partner_id'):
#                 partner = self.env['res.partner'].sudo().browse([partner_info['partner_id']])[0]
#         if email and email in [val[1] for val in result[self.ids[0]]]:  # already existing email -> skip
#             return result
#         # if partner and partner in self.message_partner_ids:  # recipient already in the followers -> skip
#         #     return result
#         if partner and partner.id in [val[0] for val in result[self.ids[0]]]:  # already existing partner ID -> skip
#             return result
#         if partner and partner.email:  # complete profile: id, name <email>
#             result[self.ids[0]].append((partner.id, partner.email_formatted, reason))
#         elif partner:  # incomplete profile: id, name
#             result[self.ids[0]].append((partner.id, '%s' % (partner.name), reason))
#         else:  # unknown partner, we are probably managing an email address
#             result[self.ids[0]].append((False, email, reason))
#         return result
#
#     def _message_get_suggested_recipients(self):
#         """ Returns suggested recipients for ids. Those are a list of
#         tuple (partner_id, partner_name, reason), to be managed by Chatter. """
#         result = super(Thread, self)._message_get_suggested_recipients()
#         for obj in self.sudo():  # SUPERUSER because of a read on res.users that would crash otherwise
#             if not obj.message_partner_ids:
#                 continue
#             for partner in obj.message_partner_ids:
#                 reason =  "" if 'user_id' not in self._fields else self._fields['user_id'].string
#                 obj._message_add_suggested_recipient(result, partner=partner, reason=reason)
#         return result
#
#     @api.returns('mail.message', lambda value: value.id)
#     def message_post(self, *,
#                      body='', subject=None, message_type='notification',
#                      email_from=None, author_id=None, parent_id=False,
#                      subtype_xmlid=None, subtype_id=False, partner_ids=None, channel_ids=None,
#                      attachments=None, attachment_ids=None,
#                      add_sign=True, record_name=False,
#                      **kwargs):
#         """ Post a new message in an existing thread, returning the new
#             mail.message ID.
#             :param str body: body of the message, usually raw HTML that will
#                 be sanitized
#             :param str subject: subject of the message
#             :param str message_type: see mail_message.message_type field. Can be anything but
#                 user_notification, reserved for message_notify
#             :param int parent_id: handle thread formation
#             :param int subtype_id: subtype_id of the message, mainly use fore
#                 followers mechanism
#             :param list(int) partner_ids: partner_ids to notify
#             :param list(int) channel_ids: channel_ids to notify
#             :param list(tuple(str,str), tuple(str,str, dict) or int) attachments : list of attachment tuples in the form
#                 ``(name,content)`` or ``(name,content, info)``, where content is NOT base64 encoded
#             :param list id attachment_ids: list of existing attachement to link to this message
#                 -Should only be setted by chatter
#                 -Attachement object attached to mail.compose.message(0) will be attached
#                     to the related document.
#             Extra keyword arguments will be used as default column values for the
#             new mail.message record.
#             :return int: ID of newly created mail.message
#         """
#         self.ensure_one()  # should always be posted on a record, use message_notify if no record
#         # split message additional values from notify additional values
#         msg_kwargs = dict((key, val) for key, val in kwargs.items() if key in self.env['mail.message']._fields)
#         notif_kwargs = dict((key, val) for key, val in kwargs.items() if key not in msg_kwargs)
#
#         if self._name == 'mail.thread' or not self.id or message_type == 'user_notification':
#             raise ValueError('message_post should only be call to post message on record. Use message_notify instead')
#
#         if 'model' in msg_kwargs or 'res_id' in msg_kwargs:
#             raise ValueError("message_post doesn't support model and res_id parameters anymore. Please call message_post on record.")
#         if 'subtype' in kwargs:
#             raise ValueError("message_post doesn't support subtype parameter anymore. Please give a valid subtype_id or subtype_xmlid value instead.")
#
#         self = self._fallback_lang() # add lang to context imediatly since it will be usefull in various flows latter.
#
#         # Explicit access rights check, because display_name is computed as sudo.
#         self.check_access_rights('read')
#         self.check_access_rule('read')
#         record_name = record_name or self.display_name
#
#         partner_ids = set(partner_ids or [])
#         channel_ids = set(channel_ids or [])
#
#         if any(not isinstance(pc_id, int) for pc_id in partner_ids | channel_ids):
#             raise ValueError('message_post partner_ids and channel_ids must be integer list, not commands')
#
#         # Find the message's author
#         author_id, email_from = self._message_compute_author(author_id, email_from, raise_exception=True)
#
#         if subtype_xmlid:
#             subtype_id = self.env['ir.model.data'].xmlid_to_res_id(subtype_xmlid)
#         if not subtype_id:
#             subtype_id = self.env['ir.model.data'].xmlid_to_res_id('mail_mt_note')
#
#         # automatically subscribe recipients if asked to
#         if self._context.get('mail_post_autofollow') and partner_ids:
#             self.message_subscribe(list(partner_ids))
#
#         MailMessage_sudo = self.env['mail.message'].sudo()
#         if self._mail_flat_thread and not parent_id:
#             parent_message = MailMessage_sudo.search([('res_id', '=', self.id), ('model', '=', self._name), ('message_type', '!=', 'user_notification')], order="id ASC", limit=1)
#             # parent_message searched in sudo for performance, only used for id.
#             # Note that with sudo we will match message with internal subtypes.
#             parent_id = parent_message.id if parent_message else False
#         elif parent_id:
#             old_parent_id = parent_id
#             parent_message = MailMessage_sudo.search([('id', '=', parent_id), ('parent_id', '!=', False)], limit=1)
#             # avoid loops when finding ancestors
#             processed_list = []
#             if parent_message:
#                 new_parent_id = parent_message.parent_id and parent_message.parent_id.id
#                 while (new_parent_id and new_parent_id not in processed_list):
#                     processed_list.append(new_parent_id)
#                     parent_message = parent_message.parent_id
#                 parent_id = parent_message.id
#
#         cc_partner_ids = set()
#         cc_recipient_ids = kwargs.pop('cc_recipient_ids', [])
#         for partner_id in cc_recipient_ids:
#             if isinstance(partner_id, (list, tuple)) and partner_id[0] == 4 \
#                     and len(partner_id) == 2:
#                 cc_partner_ids.add(partner_id[1])
#             if isinstance(partner_id, (list, tuple)) and partner_id[0] == 6 \
#                     and len(partner_id) == 3:
#                 cc_partner_ids |= set(partner_id[2])
#             elif isinstance(partner_id, int):
#                 cc_partner_ids.add(partner_id)
#             else:
#                 pass
#         bcc_partner_ids = set()
#         bcc_recipient_ids = kwargs.pop('bcc_recipient_ids', [])
#         for partner_id in bcc_recipient_ids:
#             if isinstance(partner_id, (list, tuple)) and partner_id[0] == 4 and len(partner_id) == 2:
#                 bcc_partner_ids.add(partner_id[1])
#             if isinstance(partner_id, (list, tuple)) and partner_id[0] == 6 and len(partner_id) == 3:
#                 bcc_partner_ids |= set(partner_id[2])
#             elif isinstance(partner_id, int):
#                 bcc_partner_ids.add(partner_id)
#             else:
#                 pass
#
#         values = dict(msg_kwargs)
#         values.update({
#             'author_id': author_id,
#             'email_from': email_from,
#             'model': self._name,
#             'res_id': self.id,
#             'body': body,
#             'subject': subject or False,
#             'message_type': message_type,
#             'parent_id': parent_id,
#             'subtype_id': subtype_id,
#             'partner_ids': partner_ids,
#             'channel_ids': channel_ids,
#             'add_sign': add_sign,
#             'record_name': record_name,
#             'cc_recipient_ids': [(4, pid.id) for pid in cc_recipient_ids],
#             'bcc_recipient_ids': [(4, pid.id) for pid in bcc_recipient_ids]
#         })
#         attachments = attachments or []
#         attachment_ids = attachment_ids or []
#         attachement_values = self._message_post_process_attachments(attachments, attachment_ids, values)
#         values.update(attachement_values)  # attachement_ids, [body]
#
#         new_message = self._message_create(values)
#
#         # Set main attachment field if necessary
#         self._message_set_main_attachment_id(values['attachment_ids'])
#
#         if values['author_id'] and values['message_type'] != 'notification' and not self._context.get('mail_create_nosubscribe'):
#             if self.env['res.partner'].browse(values['author_id']).active:  # we dont want to add odoobot/inactive as a follower
#                 self._message_subscribe([values['author_id']])
#
#         self._message_post_after_hook(new_message, values)
#         self._notify_thread(new_message, values, **notif_kwargs)
#         return new_message
