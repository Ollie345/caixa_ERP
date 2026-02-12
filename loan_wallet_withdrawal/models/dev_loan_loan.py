# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class DevLoanLoan(models.Model):
    _inherit = 'dev.loan.loan'
    
    withdrawal_ids = fields.One2many(
        'loan.wallet.withdrawal',
        'loan_id',
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
        """Compute total number of withdrawal requests for this loan"""
        for loan in self:
            loan.withdrawal_count = len(loan.withdrawal_ids)
    
    def action_view_withdrawals(self):
        """Open withdrawal requests for this loan"""
        self.ensure_one()
        action = {
            'name': _('Withdrawal Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'loan.wallet.withdrawal',
            'view_mode': 'list,form',
            'domain': [('loan_id', '=', self.id)],
            'context': {'default_loan_id': self.id, 'default_partner_id': self.client_id.id},
        }
        return action
