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

{
    'name': "Associated products",
    'version': '1.0',
    'category': 'Sales Management',
    'description': """This module adds associated products""",
    'author': 'Pexego Sistemas Informáticos',
    'website': '',
    "depends": ['base',
                'product',
                'sale',
                'sale_commission'],
    "data": ['security/ir.model.access.csv',
              'views/product_view.xml'],
    "installable": True
}
