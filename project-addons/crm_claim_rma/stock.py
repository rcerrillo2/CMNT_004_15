# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from odoo import api, fields, models, exceptions

class stock_picking(models.Model):

    _inherit = "stock.picking"

    claim_id = fields.Many2one('crm.claim', 'Claim')


# This part concern the case of a wrong picking out. We need to create a new
# stock_move in a picking already open.
# In order to don't have to confirm the stock_move we override the create and
# confirm it at the creation only for this case
class stock_move(models.Model):

    _inherit = "stock.move"

    claim_line_id = fields.Many2one('claim.line', 'Claim Line')

    @api.multi
    def action_done(self):
        res = super(stock_move, self).action_done()

        for move in self:
            if move.claim_line_id:
                claim_line_obj = self.env['claim.line'].browse(move.claim_line_id.id)
                if claim_line_obj.claim_type == u'customer':
                    qty = claim_line_obj.product_returned_quantity
                    loc_lost = self.env.ref('crm_rma_advance_location.stock_location_carrier_loss')
                    claim_obj = claim_line_obj.claim_id
                    if claim_line_obj.equivalent_product_id:
                        rma_cost = claim_obj.rma_cost
                        if move.location_dest_id == loc_lost:
                            standard_price = claim_line_obj.product_id.standard_price
                            rma_cost += (move.picking_type_code == u'incoming') \
                            and (standard_price * qty) or 0.0
                        else:
                            standard_price = claim_line_obj.equivalent_product_id.standard_price
                            rma_cost += (move.picking_type_code == u'outgoing') \
                            and (standard_price * qty) or 0.0
                        claim_obj.rma_cost = rma_cost
                    elif  move.location_dest_id == loc_lost:
                        standard_price = claim_line_obj.product_id.standard_price
                        rma_cost = claim_obj.rma_cost
                        rma_cost += (move.picking_type_code == u'incoming') \
                                     and (standard_price * qty) or 0.0
                        claim_obj.rma_cost = rma_cost

        return res

    def create(self, cr, uid, vals, context=None):
        move_id = super(stock_move, self
                        ).create(cr, uid, vals, context=context)
        if vals.get('picking_id'):
            picking_obj = self.pool.get('stock.picking')
            picking = picking_obj.browse(cr, uid, vals['picking_id'],
                                         context=context)
            if picking.claim_id and picking.picking_type_code == u'incoming':
                self.write(cr, uid, move_id, {'state': 'confirmed'},
                           context=context)
        return move_id


    @api.multi
    def write(self, vals):
        for pick in self:
            if pick.picking_type_id.code == 'incoming':
                if 'date_expected' in vals.keys():
                    reservations = self.env['stock.reservation'].search(
                        [('product_id', '=', pick.product_id.id),
                         ('state', '=', 'confirmed')])
                    # no se necesita hacer browse.
                    # reservations = self.env['stock.reservation'].browse(reservation_ids)
                    for reservation in reservations:
                        reservation.date_planned = pick.date_expected
                        if not reservation.claim_id:
                            continue
                        followers = reservation.claim_id.message_follower_ids
                        reservation.claim_id.\
                            message_post(body="The date planned was changed.",
                                         subtype='mt_comment',
                                         partner_ids=followers)
        return super(stock_move, self).write(vals)
