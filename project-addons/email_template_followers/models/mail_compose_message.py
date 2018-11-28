###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Vauxoo (<http://vauxoo.com>).
#    All Rights Reserved
###############Credits######################################################
#    Coded by: vauxoo consultores (info@vauxoo.com)
#############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################


from odoo import models, api, SUPERUSER_ID


class MailComposeMessage(models.TransientModel):

    _inherit = 'mail.compose.message'

    @api.model
    def generate_email_for_composer(self, template_id, res_ids, fields=None):
        values = super(MailComposeMessage, self).generate_email_for_composer(template_id, res_ids, fields=fields)

        email_template_obj = self.env['mail.template']

        email_template = email_template_obj.browse(template_id)
        if values.get('partner_ids', False) and email_template.add_followers:
            partners_to_notify = set([])
            partner_follower = self.pool.get('mail.followers')

            fol_ids = partner_follower.search(SUPERUSER_ID, [
                ('res_model', '=', self.env.context.get('active_model')),
                ('res_id', '=', self.env.context.get('active_id')),
            ], context=self.env.context)

            partners_to_notify |= set(fo.partner_id.id for fo in partner_follower.browse(SUPERUSER_ID, fol_ids))

            partners_followers_notify = values.get('partner_ids', []) + list(partners_to_notify)
            values.update({'partner_ids': list(set(partners_followers_notify))})
        return values
