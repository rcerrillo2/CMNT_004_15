# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
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

from openerp import models, api, SUPERUSER_ID
from ..events.product_events import on_stock_move_change
from openerp.addons.connector.event import (on_record_create,
                    on_record_write,
                    on_record_unlink)
from openerp.addons.connector.session import ConnectorSession


class StockMove(models.Model):

    _inherit = "stock.move"

    #TODO: Debería ser al asignar un producto, al cancelarlo, al finalizarlo y al eliminar la reserve
    @api.multi
    def write(self, vals):
        res = super(StockMove, self).write(vals)
        picking_done = []
        for move in self:
            if vals.get('picking_id', False) or (vals.get('state', False) and move.picking_id):
                vals_picking = {}
                if vals.get('state', False):
                    vals_picking = {'state': vals['state']}
                else:
                    vals_picking = {'state': move.picking_id.state}
                session = ConnectorSession(self.env.cr, SUPERUSER_ID,
                                           context=self.env.context)
                if move.picking_id.id not in picking_done:
                    on_record_write.fire(session, 'stock.picking',
                                         move.picking_id.id, vals_picking)
                    picking_done.append(move.picking_id.id)

            if vals.get('state', False) and vals["state"] != "draft":
                session = ConnectorSession(self.env.cr, SUPERUSER_ID,
                                           context=self.env.context)
                on_stock_move_change.fire(session, 'stock.move',
                                          move.id)
        return res
