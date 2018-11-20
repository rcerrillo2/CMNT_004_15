# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos
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

{
    'name': "Stock customization to print",
    'version': '1.0',
    'category': 'Customization',
    'description': """This module adds associated products""",
    'author': 'Comunitea',
    'website': '',
    "depends" : ["base", "stock_valued_picking", "base_report_to_printer",
                 "custom_account", "picking_incidences",
                 "reserve_without_save_sale", "sale_display_stock",
                 "stock_reserve_sale", "product_brand", "product_pack",
                 "product_stock_unsafety","stock"],
    "data" : ["ir_attachment_view.xml",
              "stock_custom_report.xml",
              "report/stock_report.xml",
              "data/email_template.xml",
              "stock_view.xml", "partner_view.xml", 'product_view.xml',
              'sale_view.xml', 'stock_landed_costs_view.xml', 'stock_graphic_view.xml', 'security/ir.model.access.csv'],
    "installable": True
}
