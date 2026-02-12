# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LoanWalletWithdrawalRejectWizard(models.TransientModel):
    _name = 'loan.wallet.withdrawal.reject.wizard'
    _description = 'Reject Withdrawal Request'
    
    withdrawal_id = fields.Many2one(
        'loan.wallet.withdrawal',
        string='Withdrawal Request',
        required=True
    )
    
    rejection_reason = fields.Text(
        string='Rejection Reason',
        required=True,
        help='Please provide a reason for rejecting this withdrawal request'
    )
    
    def action_reject(self):
        """Confirm rejection"""
        self.ensure_one()
        if not self.rejection_reason:
            raise ValidationError(_('Rejection reason is required.'))
        
        self.withdrawal_id.action_reject_confirm(self.rejection_reason)
        return {'type': 'ir.actions.act_window_close'}
