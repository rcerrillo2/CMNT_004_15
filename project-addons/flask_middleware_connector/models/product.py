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

from openerp import models, fields, api


class ProductTemplate(models.Model):

    _inherit = "product.template"


    web = fields.Selection([('not_published', 'Not published'),
                            ('published', 'Published')], "Web",
                           default="not_published", copy=False,
                           help="Allow to publish product description "
                                "in public web service")
    show_stock_outside = fields.Boolean("Show stock outside", copy=False,
                                        help="Allow to publish stock info "
                                             "in public web service",
                                        default=True)

    @api.multi
    def write(self, vals):
        delete = True
        if vals.get('web', False):
            for record in self:
                if record.web != vals['web']:
                    delete = False
                    break
            if delete:
                del vals['web']

        if vals.get('description_sale', False):
            description_sale = vals['description_sale']
            if description_sale[-1] == '\n':
                description_sale = description_sale[0:(len(description_sale) - 2)]
                vals['description_sale'] = description_sale

        return super(ProductTemplate, self).write(vals)


class ProductProduct(models.Model):

    _inherit = "product.product"

    @api.one
    @api.depends('bom_ids')
    def compute_is_pack(self):
        if self.bom_ids:
            self.is_pack = True
        else:
            self.is_pack = False

    is_pack = fields.Boolean(compute='compute_is_pack', store=True)
