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

from odoo import models, fields, api, _, exceptions
from datetime import date


class StockContainer(models.Model):

    _name = 'stock.container'

    @api.multi
    def _set_date_expected(self):
        picking_ids = []
        for container in self:
            if container.move_ids:
                for move in container.move_ids:
                    if move.picking_id:
                        if move.picking_id not in picking_ids:
                            picking_ids.append(move.picking_id)
                date_expected = container.date_expected
                for picking in picking_ids:
                    new_vals = {'min_date': date_expected}
                    picking.write(new_vals)

        return True

    @api.multi
    @api.depends('move_ids')
    def _get_date_expected(self):
        for container in self:
            min_date = False
            if container.move_ids:
                for move in container.move_ids:
                    if move.picking_id:
                        if not min_date or min_date < move.picking_id.min_date:
                            min_date = move.picking_id.min_date
                if min_date:
                    container.date_expected = min_date

            if not container.date_expected:
                container.date_expected = fields.Date.today()

    @api.multi
    def _get_picking_ids(self):
        for container in self:
            res = []
            for line in container.move_ids:
                if line.picking_id.id not in res:
                    res.append(line.picking_id.id)
                    container.picking_ids = res

    @api.multi
    def _get_responsible(self):
        for container in self:
            responsible = ''
            if container.picking_id:
                responsible = container.picking_id.commercial
            elif container.origin:
                responsible = self.env['sale.order'].search([('name', '=', container.origin)]).user_id
            container.user_id = responsible

    name = fields.Char("Container Ref.", required=True)
    date_expected = fields.Date("Date expected", compute='_get_date_expected', inverse='_set_date_expected', readonly=False, required=False)
    move_ids = fields.One2many("stock.move", "container_id", "Moves",
                               readonly=True, copy=False)
    picking_ids = fields.One2many('stock.picking', compute='_get_picking_ids', string='Pickings', readonly=True)

    user_id = fields.Many2one(string='Responsible', compute='_get_responsible')
    company_id = fields.Many2one("res.company", "Company", required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('stock.container'))

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Container name must be unique')
    ]


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    usage = fields.Char(compute='_get_usage')
    shipping_identifier = fields.Char('Shipping identifier', size=64)
    temp = fields.Boolean("Temp.")

    @api.multi
    def _get_usage(self):
        for pick in self:
            if not pick.location_id:
                pick.usage = pick.picking_type_id.default_location_src_id
            else:
                pick.usage = pick.location_id.usage

    @api.multi
    def action_cancel(self):
        for pick in self:
            if pick.temp:
                for move in pick.move_lines:
                    if move.state == "assigned":
                        move.do_unreserve()
                    move.state = "draft"
                    move.picking_id = False
        return super(StockPicking, self).action_cancel()


class StockMove(models.Model):

    _inherit = 'stock.move'

    partner_id = fields.Many2one('res.partner', 'Partner')
    container_id = fields.Many2one('stock.container', "Container")
    subtotal_price = fields.Float('Subtotal', compute='_calc_subtotal')
    partner_ref = fields.Char(related='purchase_line_id.order_id.partner_ref')

    @api.multi
    def _calc_subtotal(self):
        for move in self:
            move.subtotal_price = move.price_unit * move.product_uom_qty

    @api.multi
    def write(self, vals):
        res = super(StockMove, self).write(vals)
        for move in self:
            move.refresh()
            if move.picking_type_id.code == 'incoming':
                if vals.get('date_expected', False):
                    self.env['stock.reservation'].\
                        reassign_reservation_dates(move.product_id)
            if vals.get('state', False) == 'assigned':
                reserv_ids = self.env["stock.reservation"].\
                    search([('move_id', '=', move.id),
                            ('sale_line_id', '!=', False)])
                if reserv_ids:
                    notify = True
                    for line in reserv_ids[0].sale_line_id.\
                            order_id.order_line:
                        if line.id != reserv_ids[0].sale_line_id.id:
                            for reserv in line.reservation_ids:
                                if reserv.state != 'assigned':
                                    notify = False
                    if notify:
                        sale = reserv_ids[0].sale_line_id.order_id
                        followers = sale.message_follower_ids
                        sale.message_post(body=_("The sale order is already assigned."),
                                          subtype='mt_comment',
                                          partner_ids=followers)
            if vals.get('container_id', False):
                container = self.env["stock.container"].\
                    browse(vals['container_id'])
                move.date_expected = container.date_expected
        return res

    @api.model
    def create(self, vals):
        res = super(StockMove, self).create(vals)
        if (vals.get('picking_type_id', False) and
                res.picking_type_id.code == 'incoming'):
            if 'date_expected' in vals.keys():
                self.env['stock.reservation'].\
                    reassign_reservation_dates(res.product_id)
        if not res.partner_id and res.picking_id.partner_id == \
                self.env.ref('purchase_picking.partner_multisupplier'):
            raise exceptions.Warning(
                _('Partner error'), _('Set the partner in the created moves'))
        return res


class StockReservation(models.Model):
    _inherit = 'stock.reservation'

    @api.model
    def reassign_reservation_dates(self, product_id):
        product_uom = product_id.uom_id
        reservations = self.search(
            [('product_id', '=', product_id.id),
             ('state', '=', 'confirmed')])
        moves = self.env['stock.move'].search(
            [('product_id', '=', product_id.id),
             ('state', '=', 'draft'),
             ('picking_type_id.code', '=', u'incoming')],
            order='date_expected')
        reservation_index = 0

        reservation_used = 0
        for move in moves:
            qty_used = 0
            product_uom_qty = move.product_uom._compute_quantity(move.product_uom_qty, product_uom)
            while qty_used < product_uom_qty and reservation_index < len(reservations):
                reservation = reservations[reservation_index]
                reservation_qty = reservation.product_uom_qty - reservation.reserved_availability
                reservation_qty = move.product_uom._compute_quantity(reservation_qty, product_uom)
                if reservation_qty - reservation_used <= product_uom_qty - qty_used:
                    reservation.date_planned = move.date_expected
                    reservation_index += 1
                    if reservation.sale_id:
                        sale = reservation.sale_id
                        followers = sale.message_follower_ids
                        sale.message_post(body=_("The date planned of the reservation was changed."),
                                          subtype='mt_comment',
                                          partner_ids=followers)
                else:
                    reservation_used += product_uom_qty - qty_used
                    break
                qty_used += reservation_qty - reservation_used
                reservation_used = 0
        while reservation_index < len(reservations):
            reservations[reservation_index].date_planned = False
            reservation_index += 1

    @api.multi
    def reassign(self):
        context = dict(self.env.context)
        context.pop('first', False)
        res = super(StockReservation, self).reassign()
        for reservation in self:
            self.with_context(context).reassign_reservation_dates(reservation.product_id)
        return res
