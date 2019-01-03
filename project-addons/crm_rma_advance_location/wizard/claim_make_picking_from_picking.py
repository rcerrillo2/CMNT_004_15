# -*- coding: utf-8 -*-
#########################################################################
#                                                                       #
#                                                                       #
#########################################################################
#                                                                       #
# crm_claim_rma for OpenERP                                             #
# Copyright (C) 2009-2012  Akretion, Emmanuel Samyn,                    #
#       Benoît GUILLOT <benoit.guillot@akretion.com>                    #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################
from odoo import fields, models, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time


class claim_make_picking_from_picking(models.TransientModel):

    _name = 'claim_make_picking_from_picking.wizard'
    _description = 'Wizard to create pickings from picking lines'

    def _get_picking_lines(self, cr, uid, context):
        return self.pool.get('stock.picking').read(cr, uid,
            context['active_id'], ['move_lines'], context=context)['move_lines']

    # Get default source location
    @api.model
    def _get_source_loc(self):
        warehouse_id = self._get_default_warehouse()
        return warehouse_id.lot_rma_id.id

    # Get default destination location
    @api.model
    def _get_dest_loc(self):
        warehouse_id = self._get_default_warehouse()
        if self.env.context.get('picking_type'):
            context_loc = self.env.context.get('picking_type')[8:]
            if context_loc != "input":
                loc_field = 'lot_%s_id' % self.env.context.get('picking_type')[8:]
            else:
                loc_field = "wh_input_stock_loc_id"
            loc_id = warehouse_id.read([loc_field])[loc_field][0]
        return loc_id

    picking_line_source_location = fields.Many2one('stock.location',
            'Source Location',
            help="Location where the returned products are from.",
            required=True, default=_get_source_loc)
    picking_line_dest_location = fields.Many2one('stock.location',
            'Dest. Location',
            help="Location where the system will stock the returned products.",
            required=True, default=_get_dest_loc)
    picking_line_ids = fields.Many2many('stock.move',
            'claim_picking_line_picking',
            'claim_picking_id',
            'picking_line_id',
            'Picking lines', default=_get_picking_lines)

    @api.model
    def _get_default_warehouse(self):
        warehouse_id=self.env['crm.claim']._get_default_warehouse()
        return warehouse_id

    def action_cancel(self,cr,uid,ids,conect=None):
        return {'type': 'ir.actions.act_window_close',}

    # If "Create" button pressed
    def action_create_picking_from_picking(self, cr, uid, ids, context=None):
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        view_obj = self.pool.get('ir.ui.view')
        if context is None: context = {}
        if context.get('p_type', False):
            p_type = context['p_type']
        else:
            p_type = 'internal'
        type_ids = self.pool.get('stock.picking.type').search(cr, uid, [('code', '=', p_type)], context=context)
        if context.get('picking_type'):
            context_type = context.get('picking_type')[8:]
            note = 'Internal picking from RMA to %s' %context_type
            name = 'Internal picking to %s' %context_type
        view_id = view_obj.search(cr, uid, [
                                            ('xml_id', '=', 'view_picking_form'),
                                            ('model', '=', 'stock.picking'),
                                            ('type', '=', 'form'),
                                            ('name', '=', 'stock.picking.form')
                                            ], context=context)[0]
        wizard = self.browse(cr, uid, ids[0], context=context)
        prev_picking = picking_obj.browse(cr, uid,
            context['active_id'], context=context)
        partner_id = prev_picking.partner_id.id
        # create picking
        '''picking_id = picking_obj.create(cr, uid, {
                    'origin': prev_picking.origin,
                    'picking_type_id': type_ids and type_ids[0],
                    'move_type': 'one', # direct
                    'state': 'draft',
                    'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'partner_id': prev_picking.partner_id.id,
                    'invoice_state': "none",
                    'company_id': prev_picking.company_id.id,
                    'location_id': wizard.picking_line_source_location.id,
                    'location_dest_id': wizard.picking_line_dest_location.id,
                    'note' : note,
                    'claim_id': prev_picking.claim_id.id,
                })
        # Create picking lines
        for wizard_picking_line in wizard.picking_line_ids:
            move_id = move_obj.create(cr, uid, {
                    'name' : wizard_picking_line.product_id.name_template, # Motif : crm id ? stock_picking_id ?
                    'priority': '0',
                    #'create_date':
                    'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'date_expected': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'product_id': wizard_picking_line.product_id.id,
                    'product_qty': wizard_picking_line.product_qty,
                    'product_uom': wizard_picking_line.product_uom.id,
                    'partner_id': prev_picking.partner_id.id,
                    'prodlot_id': wizard_picking_line.prodlot_id.id,
                    # 'tracking_id':
                    'picking_id': picking_id,
                    'state': 'draft',
                    'price_unit': wizard_picking_line.price_unit,
                    # 'price_currency_id': claim_id.company_id.currency_id.id, # from invoice ???
                    'company_id': prev_picking.company_id.id,
                    'location_id': wizard.picking_line_source_location.id,
                    'location_dest_id': wizard.picking_line_dest_location.id,
                    'note': note,
                })
            wizard_move = move_obj.write(cr, uid,
            wizard_picking_line.id,
            {'move_dest_id': move_id},
            context=context)'''
        default_picking_data = {
            'move_lines': [],
            'location_id': wizard.picking_line_source_location.id,
            'location_dest_id': wizard.picking_line_dest_location.id,
            'picking_type_id': type_ids and type_ids[0],
            'note' : note,
            'claim_id': prev_picking.claim_id.id,
            'partner_id': prev_picking.claim_id.company_id.partner_id.id
        }
        picking_id = picking_obj.copy(cr, uid, prev_picking.id, default_picking_data, context)
        for wizard_picking_line in wizard.picking_line_ids:
            default_move_data = {
                'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'date_expected': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'partner_id': prev_picking.partner_id.id,
                'picking_id': picking_id,
                'company_id': prev_picking.company_id.id,
                'location_id': wizard.picking_line_source_location.id,
                'location_dest_id': wizard.picking_line_dest_location.id,
                'note': note,
                'picking_type_id': type_ids and type_ids[0],
            }
            move_id = move_obj.copy(cr, uid, wizard_picking_line.id, default_move_data, context)

        #TODO: Migrar
        # ~ wf_service = netsvc.LocalService("workflow")
        # ~ if picking_id:
            # ~ wf_service.trg_validate(uid,
                # ~ 'stock.picking', picking_id,'button_confirm', cr)
            # ~ picking_obj.action_assign(cr, uid, [picking_id])
        domain = "[('picking_type_code','=','%s'),('partner_id','=',%s)]"%(p_type, partner_id)
        return {
            'name': '%s' % name,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'domain' : domain,
            'res_model': 'stock.picking',
            'res_id': picking_id,
            'type': 'ir.actions.act_window',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
