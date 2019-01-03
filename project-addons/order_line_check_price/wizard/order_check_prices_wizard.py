# -*- coding: utf-8 -*-
##############################################################################
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
from openerp import models, fields, api, _


class OrderCheckPricesWizard(models.TransientModel):

    _name = 'order.check.prices.wizard'

    @api.model
    def _get_default_brands(self):
        brand_lines = []
        product_brand_obj = self.env['product.brand']
        brand_param = self.env['ir.config_parameter'].get_param('search.default.brands')
        if brand_param:
            for brand in brand_param.split(','):
                product_brand_default = product_brand_obj.search([('name', '=', brand)])
                if product_brand_default:
                    brand_lines.append({'brand_id': product_brand_default.id})
        return brand_lines

    date_start = fields.Date('Date start', default=fields.Datetime.now)
    date_end = fields.Date('Date end', default=fields.Datetime.now)
    brand_list = fields.One2many('order.check.prices.wizard.brands', 'wizard_id', 'Brands', default=_get_default_brands)
    warning = fields.Char('Warning', readonly=True, translate=True, default=lambda self:
                          _("Warning! Remember that order lines prices will be compared with actual product data"))
    info = fields.Text('Info', readonly=True)

    @api.multi
    def search_order_price_changes(self):
        view = self.env.ref('order_line_check_price.order_check_prices_wizard_form_warning').id
        ctx = self.env.context.copy()
        ctx['search_default_groupby_order_id'] = True

        lines_with_changes = []
        product_tmpl_obj = self.env['product.template']
        price_type_obj = self.env['product.price.type']
        brand_filter = self.brand_list.mapped('brand_id').ids
        ids_order_line = self.env['sale.order.line'].search([('date_order', '>=', self.date_start),
                                                             ('date_order', '<=', self.date_end),
                                                             ('order_id.state', 'in',
                                                              ('progress', 'done', 'shipping_except')),
                                                             ('product_id.product_brand_id', 'in', brand_filter)])

        for line in ids_order_line:
            real_actual_price = 0
            product = line.product_id
            partner = line.order_id.partner_id
            partner_pricelist = partner.property_product_pricelist

            for rules in partner_pricelist.version_id:
                for item in rules.items_id:
                    if (item.categ_id and item.categ_id.id == product.categ_id.id) or not item.categ_id:
                        field_price_product = price_type_obj.browse([item.base])
                        real_actual_price = product_tmpl_obj._price_get([product],
                                                                        field_price_product.field)[product.id]

            if round(line.price_unit, 2) < round(real_actual_price, 2):
                lines_with_changes.append(line.id)

        self.info = (_("Total compared lines: %s \nTotal lines with different prices: %s")
                     % (str(len(ids_order_line)), str(len(lines_with_changes))))

        ctx.update({'line_list': str(lines_with_changes)})

        return {
            'type': 'ir.actions.act_window',
            'name': _('Info changes'),
            'res_model': 'order.check.prices.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'view_id': view,
            'res_id': self.id,
            'context': ctx
        }

    @api.multi
    def view_lines(self):
        view = self.env.ref('order_line_check_price.sale_order_line_price_changes_tree').id
        search_view = self.env.ref('order_line_check_price.sale_order_line_price_changes_search').id
        ctx = self.env.context.copy()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Check price changes'),
            'res_model': 'sale.order.line',
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': view,
            'search_view_id': search_view,
            'context': ctx,
            'domain': "[('id','in', " + ctx['line_list'] + ")]"
        }


class OrderCheckPricesWizardBrands(models.TransientModel):

    _name = 'order.check.prices.wizard.brands'

    wizard_id = fields.Many2one('order.check.prices.wizard')
    brand_id = fields.Many2one('product.brand', 'Brand')
