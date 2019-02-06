# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego All Rights Reserved
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
from openerp import models, fields, api


class MrpProduction(models.Model):

    _inherit = 'mrp.production'

    final_prod_lot = fields.Many2one('stock.production.lot', 'Final lot')
    type_ids = fields.Many2many(
        'mrp.customize.type', 'mrp_customizations_rel',
        'production_id', 'customization_id', 'Type')
    sale_line_id = fields.Many2one('sale.order.line', 'order line')
    sale_id = fields.Many2one(related="sale_line_id.order_id",
                              relation="sale.order", string="Sale",
                              readonly=True)
    production_name = fields.Char("Production ref", readonly=True)
    picking_out = fields.Many2one('stock.picking', "Out picking", readonly=True)
    picking_in = fields.Many2one('stock.picking', "In picking", readonly=True)

    @api.one
    def action_assign(self):
        super(MrpProduction, self).action_assign()
        for move in self.move_lines:
            if move.state == 'confirmed':
                reserv_dict = {
                    'date_validity': False,
                    'name': u"{} ({})".format(self.name, move.name),
                    'mrp_id': self.id,
                    'move_id': move.id
                }
                reservation = self.env['stock.reservation'].create(reserv_dict)
                reservation.reserve()

    @api.multi
    def action_production_end(self):
        t_quant = self.env['stock.quant']
        for production in self:
            for move in production.move_created_ids2:
                quant_ids = t_quant.browse(move.quant_ids.ids)
                quant_ids.write({'cost': move.price_unit})
                # move.update_product_price()
        return super(MrpProduction, self).action_production_end()

    @api.multi
    def action_confirm(self):
        res = super(MrpProduction, self).action_confirm()
        picking_obj = self.env['stock.picking']
        # Create out picking
        pick_out = picking_obj.create({'partner_id': self.company_id.partner_id.id,
                                       'picking_type_id': self.env.ref('stock.picking_type_out').id,
                                       'origin': self.name})
        # Update reference out picking
        self.picking_out = pick_out.id
        for move in self.move_lines:
            move.picking_id = pick_out.id

        return res

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        context2 = dict(context)
        context2.pop('default_state', False)
        return super(MrpProduction, self).create(cr, uid, vals, context=context2)


class MrpBomLine(models.Model):

    _inherit = 'mrp.bom.line'

    final_lot = fields.Boolean('Same final product lot')


class MrpProductProduceLine(models.TransientModel):

    _inherit = 'mrp.product.produce.line'

    final_lot = fields.Boolean('final lot', compute='_get_final_lot')

    @api.one
    @api.depends('product_id')
    def _get_final_lot(self):
        production = self.env['mrp.production'].browse(
            self.env.context.get('active_id', False))
        bom_line = []
        if not production.final_prod_lot:
            bom_line = self.env['mrp.bom.line'].search(
                [('bom_id', '=', production.bom_id.id),
                 ('final_lot', '=', True),
                 ('product_id', '=', self.product_id.id)])
        if bom_line:
            self.final_lot = True
        else:
            self.final_lot = False


class MrpProductProduce(models.TransientModel):

    _inherit = 'mrp.product.produce'

    final_lot = fields.Boolean('final lot', compute='_get_final_lot')
    lot_id = fields.Many2one('stock.production.lot', 'Lot', compute='_get_lot')

    @api.one
    @api.depends('final_lot')
    def _get_lot(self):
        production = self.env['mrp.production'].browse(
            self.env.context.get('active_id'))
        if production.final_prod_lot:
            self.lot_id = production.final_prod_lot

    @api.multi
    def do_produce(self):
        production_id = self.env.context.get('active_id', False)
        assert production_id, \
            "Production Id should be specified in context as a Active ID."
        production = self.env['mrp.production'].browse(production_id)
        if not self.lot_id and self.final_lot:
            for line in self.consume_lines:
                if line.final_lot and line.lot_id:
                    self.lot_id = self.env['stock.production.lot'].create(
                        {'name': line.lot_id.name,
                         'product_id': production.product_id.id}).id
        super(MrpProductProduce, self).do_produce()
        return True

# TODO: Migrar
    # ~ @api.one
    # ~ @api.depends('consume_lines')
    # ~ def _get_final_lot(self):
        # ~ final_lot = False
        # ~ production = self.env['mrp.production'].browse(
            # ~ self.env.context.get('active_id'))
        # ~ for line in self.consume_lines:
            # ~ if line.final_lot:
                # ~ final_lot = True
        # ~ if production.final_prod_lot:
            # ~ final_lot = True
        # ~ self.final_lot = final_lot


# TODO: Migrar
# ~ class StockMoveConsume(models.TransientModel):

    # ~ _inherit = 'stock.move.consume'

    # ~ final_lot = fields.Boolean('final lot')

    # ~ @api.model
    # ~ def default_get(self, fields):
        # ~ res = super(StockMoveConsume, self).default_get(fields)
        # ~ move = self.env['stock.move'].browse(self.env.context['active_id'])
        # ~ if 'final_lot' in fields:
            # ~ bom_line = self.env['mrp.bom.line'].search(
                # ~ [('bom_id', '=', move.raw_material_production_id.bom_id.id),
                 # ~ ('final_lot', '=', True),
                 # ~ ('product_id', '=', move.product_id.id)])
            # ~ res.update({'final_lot': bom_line and bom_line.final_lot or False})
        # ~ return res

    # ~ @api.one
    # ~ def do_move_consume(self):
        # ~ move = self.env['stock.move'].browse(self.env.context['active_id'])
        # ~ if self.final_lot:
            # ~ production_lot = self.env['stock.production.lot'].create(
                # ~ {'name': self.restrict_lot_id.name,
                 # ~ 'product_id': move.raw_material_production_id.product_id.id})
            # ~ move.raw_material_production_id.final_prod_lot = production_lot
        # ~ return super(StockMoveConsume, self).do_move_consume()
