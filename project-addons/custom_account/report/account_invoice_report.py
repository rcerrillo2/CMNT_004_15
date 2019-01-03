# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
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
from odoo import models, fields
#TODO: MIgrar
# ~ from openerp.addons.account.report.account_print_overdue import Overdue


# ~ class report_overdue(models.AbstractModel):
    # ~ _name = 'report.account.report_overdue_custom'
    # ~ _inherit = 'report.abstract_report'
    # ~ _template = 'account.report_overdue_custom'
    # ~ _wrapped_report_class = Overdue


class account_invoice_report(models.Model):

    _inherit = 'account.invoice.report'

    payment_mode_id = fields.Many2one('account.payment.mode', 'Payment mode')
    number = fields.Char('Number')
    benefit = fields.Float('Benefit')
    brand_name = fields.Char('Brand name')
    area_id = fields.Many2one('res.partner.area', 'Area')
    commercial_region_ids = fields.Many2many(related='area_id.commercial_region_ids')

    def _select(self):
        select_str = super(account_invoice_report, self)._select()
        select_str += ', sub.payment_mode_id as payment_mode_id,' \
                      ' sub.number as number' \
                      ", CASE WHEN sub.type IN ('out_refund') THEN -sub.benefit " \
                      " WHEN sub.type IN ('out_invoice') THEN sub.benefit " \
                      " ELSE 0 END as benefit" \
                      ', sub.name as brand_name, sub.area_id'
        return select_str

    def _sub_select(self):
        select_str = super(account_invoice_report, self)._sub_select()
        select_str += ', ai.payment_mode_id,' \
                      ' ai.number ' \
                      ', sum(ail.quantity * ail.price_unit * (100.0-ail.discount) ' \
                      '/ 100.0) - sum(coalesce(ail.cost_unit, 0)*ail.quantity) as benefit, ' \
                      'pb.name, rpa.id as area_id'
        return select_str

    def _from(self):
        from_str = super(account_invoice_report, self)._from()
        from_str += ' LEFT JOIN product_brand pb ON pt.product_brand_id = pb.id ' \
                    ' LEFT JOIN res_partner_area rpa ON rpa.id = partner.area_id '
        return from_str

    def _group_by(self):
        group_by_str = super(account_invoice_report, self)._group_by()
        group_by_str += ', ai.payment_mode_id,' \
                        ' ai.number,' \
                        ' pb.name, ' \
                        ' rpa.id'

        return group_by_str
