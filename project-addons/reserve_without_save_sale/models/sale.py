# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api
import odoo.addons.decimal_precision as dp


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    state = fields.Selection(selection_add=[('reserve', 'Reserved')])

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.state == 'reserve':
            res.order_reserve()
        return res

    def order_reserve(self):
        self.write({'state': 'reserve'})
        lines = self.mapped('order_line').filtered(
            lambda r: r.product_id and r.product_id.type != 'service')
        lines.stock_reserve()
        return True


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    unique_js_id = fields.Char('', size=64, copy=False)
    temp_unique_js_id = fields.Char('', size=64, copy=False)
    qty_reserved = fields.Float(readonly=True,
                                related='product_id.reservation_count',
                                digits=dp.get_precision('Product Unit \
                                                  of Measure'))

    def _test_block_on_reserve(self, vals):
        super()._test_block_on_reserve(vals)
        return False

    @api.multi
    def write(self, vals):
        ctx = dict(self.env.context)
        for line in self:
            unique_js_id = vals.get('unique_js_id', line.unique_js_id)
            temp_unique_js_id = vals.get('temp_unique_js_id',
                                         line.temp_unique_js_id)

            if temp_unique_js_id:
                if vals.get('reservation_ids', False):
                    vals.pop('reservation_ids')
                if unique_js_id:
                    reserve_to_delete = self.env['stock.reservation'].search(
                        [('unique_js_id', '=', unique_js_id)])
                    if reserve_to_delete:
                        reserve_to_delete.unlink()
                elif line.reservation_ids:
                    line.reservation_ids.unlink()
                new_reserv = self.env['stock.reservation'].search(
                    [('unique_js_id', '=', temp_unique_js_id)])
                if new_reserv:
                    new_reserv.sale_line_id = line.id
                    new_reserv.origin = line.order_id.name
                else:
                    ctx['later'] = True
                vals['unique_js_id'] = temp_unique_js_id
                vals['temp_unique_js_id'] = ''
        return super(SaleOrderLine, self.with_context(ctx)).write(vals)

    @api.model
    def create(self, vals):
        context2 = dict(self._context)
        context2.pop('default_state', False)
        if vals.get('temp_unique_js_id', False):
            vals['unique_js_id'] = vals['temp_unique_js_id']
            vals.pop('temp_unique_js_id', None)
            res = super(SaleOrderLine, self.with_context(context2)).create(
                vals)
            reserve = self.env['stock.reservation'].search(
                [('unique_js_id', '=', res.unique_js_id)])
            if reserve:
                reserve.sale_line_id = res.id
                reserve.origin = res.order_id.name
        else:
            res = super(SaleOrderLine, self.with_context(context2)).create(
                vals)
        return res

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        if 'unique_js_id' in fields:
            reserv_obj = self.env['stock.reservation']
            for line in self:
                self._cr.execute("select sale_order.state, unique_js_id from "
                                 "sale_order_line inner join sale_order on "
                                 "sale_order.id = sale_order_line.order_id "
                                 "where sale_order_line.id = %s"
                                 % str(line.id))
                line_data = self._cr.fetchone()
                if line_data and line_data[0] == "reserve" and line_data[1]:
                    reserves = reserv_obj.search([('unique_js_id', '=',
                                                   line_data[1]),
                                                  ('state', '!=',
                                                   'cancel')])
                    while len(reserves) > 1:
                        reserv = reserves.pop()
                        reserv_obj.unlink(reserv)
                    if reserves and not reserves[0].sale_line_id:
                        reserves[0].sale_line_id = line.id
                        reserves[0].origin = line.order_id.name

        return super().read(fields=fields, load=load)

    @api.multi
    def unlink(self):
        for line in self:
            if line.unique_js_id:
                reserve = self.env['stock.reservation'].search(
                    [('unique_js_id', '=', line.unique_js_id)])
                reserve.unlink()
            if line.temp_unique_js_id:
                reserve = self.env['stock.reservation'].search(
                    [('unique_js_id', '=', line.temp_unique_js_id)])
                reserve.unlink()
        return super().unlink()

    def stock_reserve(self):
        if self.env.context.get('later', False):
            return True

        for line in self:
            if line.order_id.state in ('draft', 'sent', 'progress', 'done',
                                       'manual'):
                continue
            if not line.is_stock_reservable:
                continue
            if line.reservation_ids:
                for reserve in line.reservation_ids:
                    reserve.reassign()
            else:
                vals = line._prepare_stock_reservation()
                reservation = self.env['stock.reservation'].create(vals)
                reservation.reserve()
        return True
