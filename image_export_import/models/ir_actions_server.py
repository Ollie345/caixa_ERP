# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import UserError


class IrActionsServer(models.Model):
    _inherit = 'ir.actions.server'

    @api.model
    def _get_eval_context(self, action=None):
        """Add helper method to create export image action"""
        eval_context = super()._get_eval_context(action=action)
        eval_context['export_images'] = self._export_images_action
        return eval_context

    def _export_images_action(self, records):
        """Helper method to open export wizard"""
        if not records:
            raise UserError(_('Please select records to export images from.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Export Images'),
            'res_model': 'image.export.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': records._name,
                'active_ids': records.ids,
            }
        }
