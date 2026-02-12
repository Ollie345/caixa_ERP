# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    withdrawal_ids = fields.One2many(
        'loan.wallet.withdrawal',
        'partner_id',
        string='Withdrawal Requests',
        domain=[('state', '!=', 'cancelled')]
    )
    
    withdrawal_count = fields.Integer(
        string='Withdrawal Count',
        compute='_compute_withdrawal_count',
        store=False
    )
    
    @api.depends('withdrawal_ids')
    def _compute_withdrawal_count(self):
        """Compute total number of withdrawal requests"""
        for partner in self:
            partner.withdrawal_count = len(partner.withdrawal_ids)
    
    def action_view_withdrawals(self):
        """Open withdrawal requests for this customer"""
        self.ensure_one()
        action = {
            'name': _('Withdrawal Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'loan.wallet.withdrawal',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
        return action
