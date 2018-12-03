# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Omar Castiñeira Saaevdra <omar@comunitea.com>$
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


class SaleOrder(models.Model):

    _inherit = "sale.order"

    urgent = fields.Boolean("Urgent")
    top_date = fields.Date("Limit date")


class ProductUom(models.Model):

    _inherit = "product.uom"

    edi_code = fields.Char("Edi code")


class ResPartner(models.Model):

    _inherit = "res.partner"

    gln = fields.Char("GLN")


class PaymentMode(models.Model):

    _inherit = "account.payment.mode"

    edi_code = fields.Char("Edi code")
