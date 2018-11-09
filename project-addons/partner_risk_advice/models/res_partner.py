##############################################################################
#
#    Copyright (C) 2014 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Kiko Sánchez <kiko@comunitea.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields, models, api
from odoo.tools.translate import _

WARNING_MESSAGE = [
                   ('no-message', "No Message"),
                   ('warning', "Warning"),
                   ('block', "Blocking Message")
                   ]

WARNING_HELP = _("Selecting the 'Warning' option will notify user with the message, "
                 "Selecting 'Blocking Message' will throw an exception with the message and block the flow. "
                 "The Message has to be written in the next field.")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    risk_advice_ids = fields.One2many('partner.risk.advice', 'partner_id')
    rma_warn = fields.Selection(WARNING_MESSAGE, 'Invoice', help=WARNING_HELP, required=True, default='no-message')
    rma_warn_msg = fields.Text('Message for RMA')


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    # def onchange_partner_id(self, cr, uid, ids, part, email=False, context=None):
    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        import ipdb
        ipdb.set_trace()
        if not self.id:
            return {}
        warning = {}
        title = False
        message = False
        partner = self.pool.get('res.partner').browse([self.id])
        if partner.rma_warn != 'no-message':
            title = _("Warning for %s") % partner.name
            message = partner.rma_warn_msg
            warning = {
                'title': title,
                'message': message,
            }
            if partner.rma_warn == 'block':
                return {'value': {'partner_id': False}, 'warning': warning}
        result = super(CrmClaim, self).onchange_partner_id()

        if result.get('warning', False):
            warning['title'] = title and title +' & '+ result['warning']['title'] or result['warning']['title']
            warning['message'] = message and message + ' ' + result['warning']['message'] or result['warning']['message']

        if warning:
            result['warning'] = warning
        return result

    # Descomentar para probar el cron con el botón en el formulario partner
    #@api.multi
    #def check_partner_risk(self):
    #    e = self.env['partner.risk.advice'].check_partner_risk()
