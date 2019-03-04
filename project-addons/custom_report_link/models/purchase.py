# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    def print_quotation(self):
        super().print_quotation()
        return self.env.ref(
            'purchase.report_purchasequotation_custom').report_action(self)
