from odoo import models, fields, api

class DevLoanApproveWizard(models.TransientModel):
    _name = 'dev.loan.approve.wizard'
    _description = 'Approve Loan Wizard'

    loan_id = fields.Many2one('dev.loan.loan', string="Loan")
    approval_reason = fields.Text('Approval Reason', required=True)

    def action_confirm_approve(self):
        """Call the loan's approve method and pass the reason"""
        self.loan_id.action_approve_loan(reason=self.approval_reason)
        return {'type': 'ir.actions.act_window_close'}
