#########################################################################
#                                                                       #
#                                                                       #
#########################################################################
#                                                                       #
# crm_claim_rma for OpenERP                                             #
# Copyright (C) 2009-2012  Akretion, Emmanuel Samyn,                    #
#       Benoît GUILLOT <benoit.guillot@akretion.com>                    #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################
from odoo import models, fields


class ClaimMakePicking(models.TransientModel):

    _inherit = "claim_make_picking.wizard"

    def _get_dest_loc(self):
        """ Get default destination location """
        loc_id = super(ClaimMakePicking, self)._get_dest_loc()
        warehouse = self.env['stock.warehouse'].browse(self.env.context.get('warehouse_id'))
        if self.env.context.get('picking_type') == 'in':
            loc_id = warehouse.lot_rma_id
        elif self.env.context.get('picking_type') == 'loss':
            loc_id = warehouse.lot_carrier_loss_id
        return loc_id

    claim_line_dest_location = fields.Many2one("stock.location", default=_get_dest_loc)
