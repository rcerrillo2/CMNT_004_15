# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2013 Camptocamp SA
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

from odoo import models, fields, api


class sale_stock_reserve(models.TransientModel):
    _name = 'sale.stock.reserve'

    @api.model
    def _default_location_id(self):
        reserv_obj = self.env['stock.reservation']
        return reserv_obj._default_location_id()

    @api.model
    def _default_location_dest_id(self):
        reserv_obj = self.env['stock.reservation']
        return reserv_obj._default_location_dest_id()

    location_id = fields.Many2one('stock.location', 'Source Location',
                                  required=True, default=_default_location_id)
    location_dest_id = fields.\
        Many2one('stock.location', 'Reservation Location', required=True,
                 help="Location where the system will reserve the products.",
                 default=_default_location_dest_id)
    date_validity = fields.\
        Date("Validity Date",
             help="If a date is given, the reservations will be released "
                  "at the end of the validity.")
    note = fields.Text('Notes')

    @api.model
    def _prepare_stock_reservation(self, line, form):
        product_uos = line.product_uos.id if line.product_uos else False
        return {'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                'product_uom_qty': line.product_uom_qty,
                'date_validity': form.date_validity,
                'name': "{} ({})".format(line.order_id.name, line.name),
                'location_id': form.location_id.id,
                'location_dest_id': form.location_dest_id.id,
                'note': form.note,
                'product_uos_qty': line.product_uos_qty,
                'product_uos': product_uos,
                'price_unit': line.price_unit,
                'sale_line_id': line.id,
                }

    def stock_reserve(self, cr, uid, ids, line_ids, context=None):
        assert len(ids) == 1, "Expected 1 ID, got %r" % ids
        reserv_obj = self.pool.get('stock.reservation')
        line_obj = self.pool.get('sale.order.line')

        form = self.browse(cr, uid, ids[0], context=context)
        lines = line_obj.browse(cr, uid, line_ids, context=context)
        for line in lines:
            if not line.is_stock_reservable:
                continue
            vals = self._prepare_stock_reservation(line, form)
            reserv_id = reserv_obj.create(cr, uid, vals, context=context)
            reserv_obj.reserve(cr, uid, [reserv_id], context=context)
        return True

    def button_reserve(self, cr, uid, ids, context=None):
        assert len(ids) == 1, "Expected 1 ID, got %r" % ids
        if context is None:
            context = {}
        close = {'type': 'ir.actions.act_window_close'}
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        if not (active_model and active_ids):
            return close

        line_obj = self.pool.get('sale.order.line')
        if active_model == 'sale.order':
            sale_obj = self.pool.get('sale.order')
            sales = sale_obj.browse(cr, uid, active_ids, context=context)
            line_ids = [line.id for sale in sales for line in sale.order_line]

        if active_model == 'sale.order.line':
            line_ids = active_ids

        self.stock_reserve(cr, uid, ids, line_ids, context=context)
        return close
