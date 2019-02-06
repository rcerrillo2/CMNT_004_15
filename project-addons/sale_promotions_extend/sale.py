# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Marta Vázquez Rodríguez$ <marta@pexego.es>
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
from odoo import models, fields


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    def _get_tag_recursivity(self, cr, uid, ids, context=None):

        tags = []
        tagsa = []
        tagsb = []

        for t in self.pool.get('product.tag').browse(cr, uid, ids, context):
            tagsb.append(t.id)
            if t.parent_id:
                tagsa = self._get_tag_recursivity(cr, uid, [t.parent_id.id],
                                             context)
                if tagsa:
                    tags = list(set(tagsa + tagsb))
        if tags:
            return tags
        else:
            return tagsb

    def _get_tags_product(self, cr, uid, ids, field_name, arg,
                                  context=None):
        result = {}
        for line in self.browse(cr, uid, ids, context=context):
            result[line.id] = ''
            tag_obj = self.pool.get('product.tag')
            stream = []
            tags = []
            if line.product_id and line.product_id.tag_ids:
                tag_ids = [x.id for x in line.product_id.tag_ids]
                tags = self._get_tag_recursivity(cr, uid,
                                                 tag_ids,
                                                 context)
                if tags:
                    for tag in tag_obj.browse(cr, uid, tags):
                        stream.append(tag.name)
            if stream:
                result[line.id] = u", ".join(stream)
        return result

    product_tags = fields.Char(eompute="_get_tags_product", string='Tags')
    web_discount = fields.Boolean('Web Discount')
    accumulated_promo = fields.Boolean(default=False)


class SaleOrder(models.Model):

    _inherit = "sale.order"

    no_promos = fields.Boolean("Not apply promotions", help="Reload the prices after marking this check")

    def apply_promotions(self, cursor, user, ids, context=None):
        if context is None:
            context = {}
        context2 = dict(context)
        context2.pop('default_state', False)
        self._prepare_custom_line(cursor, user, ids, moves=False,
                                  context=context2)
        order = self.browse(cursor, user, ids[0], context=context2)
        promotions_obj = self.pool.get('promos.rules')

        if not order.no_promos:
            res = super(SaleOrder, self).apply_promotions(cursor, user, ids,
                                                          context=context2)
        else:
            self.clear_existing_promotion_lines(cursor, user, ids[0], context)
            promotions_obj.apply_special_promotions(cursor, user, ids[0], context=None)
            res = False

        if order.state == 'reserve':
            order.order_reserve()

        taxes = order.order_line.filtered(lambda l: len(l.tax_id) > 0)[0].tax_id
        for line in order.order_line:
            if line.promotion_line:
                line.tax_id = taxes
                if '3 por ciento' in line.name:
                    line.sequence = 999

        return res

    def clear_existing_promotion_lines(self, cursor, user,
                                       order_id, context=None):
        order = self.browse(cursor, user, order_id, context)
        order_line_obj = self.pool.get('sale.order.line')
        order_line_ids = order_line_obj.search(cursor, user,
                                               [
                                                   ('order_id', '=', order.id),
                                               ], context=context
                                               )

        line_dict = {}
        for line in order_line_obj.browse(cursor, user, order_line_ids, context):
            line_dict[line.id] = line.old_discount

        super(SaleOrder, self).clear_existing_promotion_lines(cursor, user, order_id, context=None)
        order_line_ids = order_line_obj.search(cursor, user,
                                               [
                                                   ('order_id', '=', order.id),
                                               ], context=context
                                               )

        for line in order_line_obj.browse(cursor, user, order_line_ids, context):
            # if the line has an accumulated promo and the discount of the partner is 0
            if line.accumulated_promo and line_dict[line.id] == 0.0:
                order_line_obj.write(cursor, user,
                                     [line.id],
                                     {'discount': line.old_discount,
                                      'old_discount': 0.00,
                                      'accumulated_promo': False},
                                     context=context)
            elif line.accumulated_promo:
                order_line_obj.write(cursor, user,
                                     [line.id],
                                     {'accumulated_promo': False},
                                     context=context)
