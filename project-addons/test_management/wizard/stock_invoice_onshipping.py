##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
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

from odoo import models, api, exceptions, _


class StockInvoiceOnShipping(models.TransientModel):

    _inherit = 'stock.invoice.onshipping'

    @api.multi
    def create_invoice(self):
        pick_ids = self.env.context.get('active_ids', [])
        for pick in self.env["stock.picking"].browse(pick_ids):
            if pick.tests:
                raise exceptions.Warning(_("Picking %s is not invoiceable. "
                                           "Tests") % pick.name)
        res = super(StockInvoiceOnShipping, self).create_invoice()

        return res
