# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Report check sale price changes",
    "summary": "Review changes on sale order line price",
    "version": "8.0.1.0.0",
    "category": "Uncategorized",
    "author": "Nadia Ferreyra",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
        "sale",
        "purchase_proposal"
    ],
    "data": [
        'wizard/order_check_prices_wizard_view.xml'
    ],
}
