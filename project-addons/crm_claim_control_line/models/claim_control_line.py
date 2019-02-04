# -*- coding: utf-8 -*-
from openerp import fields, models, api, exceptions, _
from openerp.exceptions import ValidationError


class CrmClaim(models.Model):
    _inherit = "crm.claim"

    @api.multi
    def make_refund_invoice(self):

        if self.claim_inv_line_ids:
            data_current_rma = {}
            for rma_invoice_line in self.claim_inv_line_ids:
                if rma_invoice_line.product_id.id in data_current_rma.keys():
                    data_current_rma[rma_invoice_line.product_id.id] = data_current_rma[rma_invoice_line.product_id.id] + rma_invoice_line.qty
                else:
                    data_current_rma[rma_invoice_line.product_id.id] = rma_invoice_line.qty

            for rma_invoice_line in self.claim_inv_line_ids:
                if (not rma_invoice_line.invoiced) and (rma_invoice_line.product_id.id):

                    qty_current_rma = rma_invoice_line.qty
                    product_current_rma = rma_invoice_line.product_id.id
                    invoice_related = rma_invoice_line.invoice_id.id

                    other_rma = self.claim_inv_line_ids.search([('invoice_id', '=', [invoice_related])])
                    data_other_rma = {}
                    data_other_rma[product_current_rma] = 0
                    for item_inv_rma in other_rma:
                        qty_other_rma = item_inv_rma.qty
                        product_other_rma = item_inv_rma.product_id.id
                        invoiced = item_inv_rma.invoiced
                        if invoiced:
                            if product_other_rma in data_other_rma.keys():
                                data_other_rma[product_other_rma] = data_other_rma[product_other_rma] + qty_other_rma
                            else:
                                data_other_rma[product_other_rma] = qty_other_rma

                    inv_line = rma_invoice_line.invoice_id.invoice_line
                    data_invoice = {}
                    for item_invoice in inv_line:
                        qty_invoice = item_invoice.quantity
                        product = item_invoice.product_id.id
                        data_invoice[product] = qty_invoice

                    if product_current_rma in data_invoice.keys():
                        qty_available = data_invoice[product_current_rma] - data_other_rma[product_current_rma]
                        if qty_available < qty_current_rma:
                            raise ValidationError(_('Product quantity can not be cover by the invoice.'))
                        if qty_available < data_current_rma[product_current_rma]:
                            raise ValidationError(_('Total product quantity can not be covered by the invoice.'))

        res = super(CrmClaim, self).make_refund_invoice()
        return res

