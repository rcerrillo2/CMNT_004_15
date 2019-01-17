# -*- coding: utf-8 -*-

from openerp import models, fields


class ResPartner(models.Model):

    _inherit = 'res.partner'

    viewer_ids = fields.Many2many('res.users', string="Allow Users")
