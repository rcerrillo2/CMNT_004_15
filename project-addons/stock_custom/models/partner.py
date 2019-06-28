# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResPartner(models.Model):

    _inherit = "res.partner"

    not_print_picking = fields.Boolean(
        help="Only print attachments on picking with attachs. report")
