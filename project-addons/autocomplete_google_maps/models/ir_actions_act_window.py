# -*- coding: utf-8 -*-
from openerp import fields, models


class IrActionsActWindow(models.Model):
    _inherit = 'ir.actions.act_window'

    view_type = fields.Selection([('tree', 'Tree'), ('form', 'Form'), ('map', 'Map')], string='View Type',
                                 required=True,
                                 help="View type: Tree type to use for the tree view, set to 'tree' for a hierarchical tree view, or 'form' for a regular list view")
