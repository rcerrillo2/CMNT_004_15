# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    @author Alberto Luengo Cabanillas
#    Copyright (C) 2016
#    Comunitea Servicios Tecnológicos (http://www.comunitea.com)
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

from odoo import models, fields, exceptions, api, _


class sale_order(models.Model):
    """

    """
    _inherit = 'sale.order'
    blocked = fields.Boolean(related='partner_id.commercial_partner_id.blocked_sales')
    defaulter = fields.Boolean(related='partner_id.commercial_partner_id.defaulter')
    allow_confirm_blocked = fields.Boolean('Allow confirm', copy=False)
    blocked_magreb = fields.Boolean(default=False)

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        """
        Comprueba si el cliente del pedido de venta está bloqueado antes de efectuar ninguna venta
        """
        if not part:
            return {'value':{'partner_invoice_id': False, 'partner_shipping_id':False, 'payment_term' : False}}
        warning = {}
        title = False
        message = False
        #Compruebo la empresa actual y su padre...
        partner_dict = self.pool.get('res.partner').read(cr, uid, part,['commercial_partner_id'])
        partner_ids_to_check = [partner_dict['commercial_partner_id'][0], part]
        unique_partner_ids_to_check = filter(lambda a: a != False,[x for i,x in enumerate(partner_ids_to_check)if x not in partner_ids_to_check[i+1:]])
        for partner_id in unique_partner_ids_to_check:
            partner_fields_dict = self.pool.get('res.partner').read(cr, uid, partner_id, ['blocked_sales', 'defaulter', 'name'])
            if partner_fields_dict['defaulter']:
                title = _("Warning for %s") % partner_fields_dict['name']
                message = _('Defaulter customer! Please contact the accounting department.')
                warning = {
                    'title': title,
                    'message': message,
                }
            elif partner_fields_dict['blocked_sales']:
                title =  _("Warning for %s") % partner_fields_dict['name']
                message = _('Customer blocked by lack of payment. Check the maturity dates of their account move lines.')
                warning = {
                        'title': title,
                        'message': message,
                }
                #return {'value': {'partner_id': False}, 'warning': warning}

        result =  super(sale_order, self).onchange_partner_id(cr, uid, ids, part, context=context)

        if result.get('warning',False):
            warning['title'] = title and title +' & '+ result['warning']['title'] or result['warning']['title']
            warning['message'] = message and message + ' ' + result['warning']['message'] or result['warning']['message']

        return {'value': result.get('value',{}), 'warning':warning}

    @api.one
    @api.onchange('partner_id', 'section_id', 'payment_term')
    def get_block_magreb (self):

        if ((self.section_id.complete_name == 'Magreb'
             and self.payment_term.name in ('Pago inmediato', 'Prepago'))
            or (self.partner_id.section_id.name == 'Magreb'
                and self.partner_id.property_payment_term_id.name in ('Pago inmediato', 'Prepago'))) \
                and self.allow_confirm_blocked is False:
            self.blocked_magreb = True
        else:
            self.blocked_magreb = False

    @api.multi
    def action_button_confirm(self):
        order = self[0]
        partner_ids_to_check = [order.partner_id.commercial_partner_id.id,
                                order.partner_id.id]
        partner_ids_to_check = list(set(partner_ids_to_check))
        message = ''
        for partner in self.env['res.partner'].browse(partner_ids_to_check):
            if partner.blocked_sales and not order.allow_confirm_blocked:
                message = _('Customer %s blocked by lack of payment. Check '
                            'the maturity dates of their account move '
                            'lines.') % partner.name
            elif partner.defaulter:
                message = _('Defaulter customer! Please contact the accounting department.')
            elif partner.customer_payment_mode.name == 'Recibo domiciliado' and len(partner.bank_ids) == 0:
                message = _('Order blocked. The client has not bank account.')

            if message:
                raise exceptions.Warning(message)

        if self.blocked_magreb and self.allow_confirm_blocked is False:
            message = _('Order blocked. The accounting department must approve this order.')
            raise exceptions.Warning(message)

        return super(sale_order, self).action_button_confirm()
