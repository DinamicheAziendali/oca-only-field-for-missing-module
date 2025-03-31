# Copyright (C) 2023-Today:
#     Dinamiche Aziendali srl (<http://www.dinamicheaziendali.it/>)
# @author: Gianmarco Conte (gconte@dinamicheaziendali.it)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).
from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.base.models.ir_mail_server import MailDeliveryException


class FatturaPAAttachmentOut(models.Model):
    _inherit = "fatturapa.attachment.out"

    # def send_via_pec(self):
    #     self._check_fetchmail()
    #     self.env.company.sdi_channel_id.check_first_pec_sending()
    #     states = self.mapped("state")
    #     if set(states) != {"ready"}:
    #         raise UserError(_("You can only send files in 'Ready to Send' state."))
    #     for att in self:
    #         if not att.datas or not att.name:
    #             raise UserError(_("File content and file name are mandatory"))
    #         self.env.company.sdi_channel_id.pec_server_id.write(
    #             {"active": True}
    #         )  # ADD for send with pec server no active
    #         mail_message = self.env["mail.message"].create(
    #             {
    #                 "model": self._name,
    #                 "res_id": att.id,
    #                 "subject": att.name,
    #                 "body": "XML file for FatturaPA {} sent to Exchange System to "
    #                 "the email address {}.".format(
    #                     att.name, self.env.company.email_exchange_system
    #                 ),
    #                 "attachment_ids": [(6, 0, att.ir_attachment_id.ids)],
    #                 "email_from": self.env.company.email_from_for_fatturaPA,
    #                 "reply_to": self.env.company.email_from_for_fatturaPA,
    #                 "mail_server_id": self.env.company.sdi_channel_id.pec_server_id.id,
    #             }
    #         )
    #
    #         mail = self.env["mail.mail"].create(
    #             {
    #                 "mail_message_id": mail_message.id,
    #                 "body_html": mail_message.body,
    #                 "email_to": self.env.company.email_exchange_system,
    #                 "headers": {
    #                     "Return-Path": self.env.company.email_from_for_fatturaPA
    #                 },
    #             }
    #         )
    #
    #         if mail:
    #             try:
    #                 mail.send(raise_exception=True)
    #                 att.state = "sent"
    #                 att.sending_date = fields.Datetime.now()
    #                 att.sending_user = self.env.user.id
    #                 self.env.company.sdi_channel_id.update_after_first_pec_sending()
    #             except MailDeliveryException as e:
    #                 att.state = "sender_error"
    #                 mail.body = str(e)
    #         self.env.company.sdi_channel_id.pec_server_id.write({"active": False})

    def send_via_pec(self):
        self._check_fetchmail()
        self.env.company.sdi_channel_id.check_first_pec_sending()
        states = self.mapped("state")
        if set(states) != {"ready"}:
            raise UserError(_("You can only send files in 'Ready to Send' state."))
        # ADD for send with pec server no active
        self.env.company.sdi_channel_id.pec_server_id.write({"active": True})
        for att in self:
            if not att.datas or not att.name:
                self.env.company.sdi_channel_id.pec_server_id.write({"active": False})
                raise UserError(_("File content and file name are mandatory"))
            mail_message = self.env["mail.message"].create(
                {
                    "model": self._name,
                    "res_id": att.id,
                    "subject": att.name,
                    "body": "XML file for FatturaPA {} sent to Exchange System to "
                    "the email address {}.".format(
                        att.name, self.env.company.email_exchange_system
                    ),
                    "attachment_ids": [(6, 0, att.ir_attachment_id.ids)],
                    "email_from": self.env.company.email_from_for_fatturaPA,
                    "reply_to": self.env.company.email_from_for_fatturaPA,
                    "mail_server_id": self.env.company.sdi_channel_id.pec_server_id.id,
                }
            )

            mail = self.env["mail.mail"].create(
                {
                    "mail_message_id": mail_message.id,
                    "body_html": mail_message.body,
                    "email_to": self.env.company.email_exchange_system,
                    "headers": {
                        "Return-Path": self.env.company.email_from_for_fatturaPA
                    },
                }
            )

            if mail:
                try:
                    mail.send(raise_exception=True)
                    att.state = "sent"
                    att.sending_date = fields.Datetime.now()
                    att.sending_user = self.env.user.id
                    self.env.company.sdi_channel_id.update_after_first_pec_sending()
                except MailDeliveryException as e:
                    att.state = "sender_error"
                    mail.body = str(e)
        self.env.company.sdi_channel_id.pec_server_id.write({"active": False})
