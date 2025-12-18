from odoo import models, fields, api

class DevLoanApproveWizard(models.TransientModel):
    _name = 'dev.loan.approve.wizard'
    _description = 'Approve Loan Wizard'

    loan_id = fields.Many2one('dev.loan.loan', string="Loan", required=True)
    approval_reason = fields.Text('Approval Reason', required=True)

    @api.model
    def default_get(self, fields_list):
        """Load loan_id from active_id"""
        res = super().default_get(fields_list)
        active_id = self._context.get('active_id')
        if active_id and 'loan_id' in fields_list:
            res['loan_id'] = active_id
        return res

    def action_confirm_approve(self):
        """Call the loan's approve method and pass the reason"""
        self.loan_id.action_approve_loan(reason=self.approval_reason)
        return {'type': 'ir.actions.act_window_close'}
