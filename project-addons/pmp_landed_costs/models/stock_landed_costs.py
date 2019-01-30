##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
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

from odoo import models, api, exceptions, _, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools import float_round


class StockLandedCost(models.Model):

    _inherit = 'stock.landed.cost'

    account_journal_id = fields.Many2one('account.journal', 'Account Journal', required=True,
                                         states={'done': [('readonly', True)]},
                                         default=lambda self: self.env['account.journal'].search([('code', '=', 'APUR')]))

    container_ids = fields.Many2many('stock.container', string='Containers', states={'done': [('readonly', True)]},
                                     copy=False, compute='_get_container')

    @api.multi
    def _get_container(self):
        for cost in self:
            move_obj = self.env['stock.move']
            container_obj = self.env['stock.container']
            res = []
            for picking_id in cost.picking_ids:
                move_id = move_obj.search([('picking_id', '=', picking_id.id), ('container_id', '!=', False)], limit=1)
                container_id = container_obj.browse(move_id.container_id.id)
                res.append(container_id.id)

            cost.container_ids = res

    @api.multi
    def compute_landed_cost(self):
        AdjustementLines = self.env['stock.valuation.adjustment.lines']
        AdjustementLines.search([('cost_id', 'in', self.ids)]).unlink()

        digits = dp.get_precision('Product Price')(self._cr)
        towrite_dict = {}
        for cost in self.filtered(lambda cost: cost.picking_ids):
            total_qty = 0.0
            total_cost = 0.0
            total_weight = 0.0
            total_volume = 0.0
            total_line = 0.0
            total_tariff = 0.0
            all_val_line_values = cost.get_valuation_lines()
            for val_line_values in all_val_line_values:
                for cost_line in cost.cost_lines:
                    val_line_values.update({'cost_id': cost.id, 'cost_line_id': cost_line.id})
                    self.env['stock.valuation.adjustment.lines'].create(val_line_values)
                total_qty += val_line_values.get('quantity', 0.0)
                total_weight += val_line_values.get('weight', 0.0)
                total_volume += val_line_values.get('volume', 0.0)
                total_tariff += val_line_values.get('tariff', 0.0)

                former_cost = val_line_values.get('former_cost', 0.0)
                # round this because former_cost on the valuation lines is also rounded
                total_cost += tools.float_round(former_cost, precision_digits=digits[1]) if digits else former_cost

                total_line += 1

            for line in cost.cost_lines:
                value_split = 0.0
                for valuation in cost.valuation_adjustment_lines:
                    value = 0.0
                    if valuation.cost_line_id and valuation.cost_line_id.id == line.id:
                        if line.split_method == 'by_quantity' and total_qty:
                            per_unit = (line.price_unit / total_qty)
                            value = valuation.quantity * per_unit
                        elif line.split_method == 'by_weight' and total_weight:
                            per_unit = (line.price_unit / total_weight)
                            value = valuation.weight * per_unit
                        elif line.split_method == 'by_volume' and total_volume:
                            per_unit = (line.price_unit / total_volume)
                            value = valuation.volume * per_unit
                        elif line.split_method == 'equal':
                            value = (line.price_unit / total_line)
                        elif line.split_method == 'by_current_cost_price' and total_cost:
                            per_unit = (line.price_unit / total_cost)
                            value = valuation.former_cost * per_unit
                        elif line.split_method == 'by_tariff' and total_tariff:
                            per_unit = (line.price_unit / total_tariff)
                            value = valuation.tariff * per_unit
                        else:
                            value = (line.price_unit / total_line)

                        if digits:
                            value = tools.float_round(value, precision_digits=digits[1], rounding_method='UP')
                            fnc = min if line.price_unit > 0 else max
                            value = fnc(value, line.price_unit - value_split)
                            value_split += value

                        if valuation.id not in towrite_dict:
                            towrite_dict[valuation.id] = value
                        else:
                            towrite_dict[valuation.id] += value
        for key, value in towrite_dict.items():
            AdjustementLines.browse(key).write({'additional_landed_cost': value})
        return True

    def get_valuation_lines(self):
        lines = []

        for move in self.mapped('picking_ids').mapped('move_lines'):
            # it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
            if move.product_id.cost_method != 'fifo':
                continue
            vals = {
                'product_id': move.product_id.id,
                'move_id': move.id,
                'quantity': move.product_qty,
                'former_cost': move.value,
                'weight': move.product_id.weight * move.product_qty,
                'volume': move.product_id.volume * move.product_qty,
                'tariff': move.product_id.tariff * move.product_qty
            }
            lines.append(vals)
        return lines

    # TODO migrar stock_custom (update_real_cost)
    # def button_validate(self):
    #     res = super(StockLandedCost, self).button_validate()
    #     for cost in self:
    #         for line in cost.valuation_adjustment_lines:
    #             if line.product_id.cost_method == 'fifo':
    #                 self.env['product.product'].update_real_cost()
    #     return res


class StockValuationAdjustmentLines(models.Model):

    _inherit = 'stock.valuation.adjustment.lines'

    standard_price = fields.Float('Standard price')
    new_standard_price = fields.Float('New standard price')
    tariff = fields.Float("Tariff", digits=(16, 2))

    @api.multi
    def write(self, vals):
        if vals.get('additional_landed_cost', False):
            vals['standard_price'] = \
                sum(self.move_id.mapped('quant_ids.inventory_value')) / \
                sum(self.move_id.mapped('quant_ids.qty'))
            vals['new_standard_price'] = (
                sum(self.move_id.mapped('quant_ids.inventory_value')) +
                vals['additional_landed_cost']) / sum(self.move_id.mapped('quant_ids.qty'))
        return super(StockValuationAdjustmentLines, self).write(vals)


class StockLandedCostLines(models.Model):
    _inherit = 'stock.landed.cost.lines'

    split_method = fields.Selection(selection_add=[('by_tariff',
                                                    'By tariff')])

    @api.onchange('product_id')
    def onchange_product_id(self):
        super(StockLandedCostLines, self).onchange_product_id()

        if self.product_id:
            stock_input_acc = self.product_id.property_stock_account_input and self.product_id.property_stock_account_input.id or False
            if not stock_input_acc:
                stock_input_acc = self.product_id.categ_id.property_stock_account_input_categ and self.product_id.categ_id.property_stock_account_input_categ.id or False
            self.account_id = stock_input_acc
