# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class DevLoanFinalRejectWizard(models.TransientModel):
    _name = 'dev.loan.final.reject.wizard'
    _description = 'Final Rejection Wizard'

    loan_id = fields.Many2one('dev.loan.loan', string='Loan', required=True)
    reject_reason = fields.Text(
        string='Rejection Reason',
        required=True,
        help='Reason for rejecting this loan'
    )

    def action_confirm_reject(self):
        """Confirm final rejection"""
        self.ensure_one()
        
        if not self.reject_reason or not self.reject_reason.strip():
            raise ValidationError(_("Rejection reason is required"))
        
        self.loan_id.action_final_approve_reject(reason=self.reject_reason)
        
        return {'type': 'ir.actions.act_window_close'}
