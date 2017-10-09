# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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
from openerp import models, api, exceptions, _


class StockSaleDeposit(models.TransientModel):
    _name = 'stock.sale.deposit'

    @api.multi
    def create_sale(self):
        deposit_obj = self.env['stock.deposit']
        deposit_ids = self.env.context.get('active_ids', [])
        deposits = deposit_obj.search([('id', 'in', deposit_ids),
                                       ('state', '=', 'draft')])
        move_obj = self.env['stock.move']
        picking_type_id = self.env.ref('stock.picking_type_out')
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type_id.id,
            'invoice_state': '2binvoiced'})

        procurement_id = None
        sorted_deposits = sorted(deposits, key=lambda deposit: deposit.sale_id.procurement_group_id)
        for deposit in sorted_deposits:
            if not picking['partner_id']:
                procurement_id = deposit.sale_id.procurement_group_id
                partner_id = deposit.partner_id.id
                commercial = deposit.user_id.id
                group_id = procurement_id.id
                picking.write({'partner_id': partner_id, 'commercial': commercial,
                               'group_id': group_id, 'origin': deposit.sale_id.name})

            elif picking['group_id'] != deposit.sale_id.procurement_group_id:
                picking = self.env['stock.picking'].create({
                    'picking_type_id': picking_type_id.id,
                    'invoice_state': '2binvoiced'})
                procurement_id = deposit.sale_id.procurement_group_id
                partner_id = deposit.partner_id.id
                commercial = deposit.user_id.id
                group_id = procurement_id.id
                picking.write({'partner_id': partner_id, 'commercial': commercial,
                               'group_id': group_id, 'origin': deposit.sale_id.name})

            values = {
                'product_id': deposit.product_id.id,
                'product_uom_qty': deposit.product_uom_qty,
                'product_uom': deposit.product_uom.id,
                'partner_id': deposit.partner_id.id,
                'name': 'Sale Deposit: ' + deposit.move_id.name,
                'location_id': deposit.move_id.location_dest_id.id,
                'location_dest_id': deposit.partner_id.property_stock_customer.id,
                'invoice_state': '2binvoiced',
                'picking_id': picking.id,
                'procurement_id': deposit.move_id.procurement_id.id,
                'commercial': deposit.user_id.id,
                'group_id': procurement_id.id
            }
            move = move_obj.create(values)
            move.action_confirm()
            move.force_assign()
            move.action_done()
            deposit.write({'state': 'sale', 'sale_move_id': move.id})
