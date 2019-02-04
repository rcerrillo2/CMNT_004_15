# -*- coding: utf-8 -*-
{
    "name": "crm_claim_control_line",
    "version": "1.0",
    "category": "crm",
    "description": """
This module will check the product quantity available in the invoiced informed into the RMA, before to create the refuse invoice.
    """,
    "author": "David Mora",
    "depends": [
        "crm_claim",
        "crm_claim_rma_custom"
    ],
    "data": [
    ],
    "installable": True
}