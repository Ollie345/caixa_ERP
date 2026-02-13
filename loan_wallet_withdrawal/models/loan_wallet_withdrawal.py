# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class LoanWalletWithdrawal(models.Model):
    _name = 'loan.wallet.withdrawal'
    _description = 'Loan Wallet Withdrawal Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        domain=[('is_allow_loan', '=', True)],
        tracking=True,
        help='Customer requesting the withdrawal'
    )
    
    loan_id = fields.Many2one(
        'dev.loan.loan',
        string='Related Loan',
        domain="[('client_id', '=', partner_id), ('state', '=', 'disburse')]",
        tracking=True,
        help='Loan associated with this withdrawal'
    )
    
    wallet_account_number = fields.Char(
        related='partner_id.wallet_account_number',
        string='Wallet Account Number',
        readonly=True,
        store=True
    )
    
    withdrawal_amount = fields.Monetary(
        string='Withdrawal Amount',
        required=True,
        tracking=True,
        currency_field='currency_id',
        help='Amount to withdraw from wallet'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    
    bank_name = fields.Char(
        string='Bank Name',
        required=True,
        tracking=True,
        help='Customer bank name for withdrawal'
    )
    
    account_number = fields.Char(
        string='Account Number',
        required=True,
        tracking=True,
        help='Customer bank account number'
    )
    
    account_name = fields.Char(
        string='Account Name',
        required=True,
        tracking=True,
        help='Customer bank account name'
    )
    
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Submitted for Approval'),
            ('approved', 'Approved'),
            ('done', 'Done'),
            ('rejected', 'Rejected'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        copy=False
    )
    
    transaction_id = fields.Char(
        string='Transaction ID',
        tracking=True,
        copy=False,
        help='Transaction ID from external payment system (required before completion)'
    )
    
    is_verified = fields.Boolean(
        string='Withdrawal Verified',
        copy=False,
        default=False,
        help='Confirmed by BaaS verification logic'
    )
    
    request_date = fields.Date(
        string='Request Date',
        default=fields.Date.context_today,
        required=True,
        tracking=True
    )
    
    approval_date = fields.Datetime(
        string='Approval Date',
        readonly=True,
        copy=False
    )
    
    approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
        readonly=True,
        copy=False
    )
    
    completion_date = fields.Datetime(
        string='Completion Date',
        readonly=True,
        copy=False
    )
    
    completed_by = fields.Many2one(
        'res.users',
        string='Completed By',
        readonly=True,
        copy=False
    )
    
    rejection_reason = fields.Text(
        string='Rejection Reason',
        copy=False
    )
    
    rejected_by = fields.Many2one(
        'res.users',
        string='Rejected By',
        readonly=True,
        copy=False
    )
    
    notes = fields.Text(
        string='Notes',
        help='Additional notes or comments'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    
    @api.model
    def create(self, vals):
        """Generate sequence number for withdrawal request"""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('loan.wallet.withdrawal') or _('New')
        return super().create(vals)
    
    @api.constrains('withdrawal_amount')
    def _check_withdrawal_amount(self):
        """Validate withdrawal amount is positive"""
        for record in self:
            if record.withdrawal_amount <= 0:
                raise ValidationError(_('Withdrawal amount must be greater than zero.'))
    
    @api.constrains('transaction_id', 'state')
    def _check_transaction_id(self):
        """Ensure transaction ID is provided before moving to done state"""
        for record in self:
            if record.state == 'done' and not record.transaction_id:
                raise ValidationError(_('Transaction ID is required before marking withdrawal as Done.'))
    
    def action_submit(self):
        """Submit withdrawal request for approval"""
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_('Only draft withdrawals can be submitted.'))
            
            if not record.partner_id.wallet_account_number:
                raise ValidationError(_('Customer does not have a wallet account number.'))
            
            record.state = 'submitted'
            record.message_post(
                body=_('Withdrawal request submitted for approval.')
            )
    
    def action_approve(self):
        """Approve withdrawal request"""
        for record in self:
            if record.state not in ['submitted', 'draft']:
                raise ValidationError(_('Only submitted or draft withdrawals can be approved.'))
            
            record.write({
                'state': 'approved',
                'approval_date': fields.Datetime.now(),
                'approved_by': self.env.user.id,
            })
            record.message_post(
                body=_('Withdrawal request approved by %s.') % self.env.user.name
            )
    
    def action_reject(self):
        """Open rejection wizard"""
        return {
            'name': _('Reject Withdrawal Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'loan.wallet.withdrawal.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_withdrawal_id': self.id},
        }
    
    def action_reject_confirm(self, reason):
        """Confirm rejection with reason"""
        for record in self:
            record.write({
                'state': 'rejected',
                'rejection_reason': reason,
                'rejected_by': self.env.user.id,
            })
            record.message_post(
                body=_('Withdrawal request rejected by %s.\nReason: %s') % (self.env.user.name, reason)
            )
    
    def action_verify_withdrawal(self):
        """Verify the withdrawal transaction against BaaS API."""
        self.ensure_one()
        if not self.transaction_id:
            raise ValidationError(_("Please enter a Transaction ID first."))
            
        res = self.env['baas.service'].get_transaction_details(self.transaction_id)
        
        if not res.get('success'):
            raise ValidationError(_("Verification Failed: %s") % res.get('message'))
            
        # Amount Validation
        if round(res.get('amount'), 2) != round(self.withdrawal_amount, 2):
            raise ValidationError(_("Amount Mismatch! BaaS shows %s, but Withdrawal is %s") % (res.get('amount'), self.withdrawal_amount))
            
        # Bank Account Validation
        if res.get('account_number') != self.account_number:
            raise ValidationError(_("Account Number Mismatch! BaaS shows recipient %s, but Withdrawal bank account is %s") % (res.get('account_number'), self.account_number))
            
        # Status Validation
        if res.get('status') not in ['SUCCESSFUL', 'SUCCESS']:
             raise ValidationError(_("Transaction is not successful according to BaaS (Status: %s)") % res.get('status'))

        self.is_verified = True
        return True

    def action_done(self):
        """Mark withdrawal as done (requires verified transaction ID)"""
        for record in self:
            if record.state != 'approved':
                raise ValidationError(_('Only approved withdrawals can be marked as done.'))
            
            if not record.is_verified:
                raise ValidationError(_("The withdrawal transaction has not been verified yet. Please click 'Verify Withdrawal' first."))
            
            if not record.transaction_id:
                raise ValidationError(_('Transaction ID is required before marking withdrawal as Done.'))
            
            record.write({
                'state': 'done',
                'completion_date': fields.Datetime.now(),
                'completed_by': self.env.user.id,
            })
            record.message_post(
                body=_('Withdrawal completed by %s.\nTransaction ID: %s') % (self.env.user.name, record.transaction_id)
            )
    
    def action_cancel(self):
        """Cancel withdrawal request"""
        for record in self:
            if record.state in ['done', 'rejected']:
                raise ValidationError(_('Cannot cancel completed or rejected withdrawals.'))
            
            record.state = 'cancelled'
            record.message_post(
                body=_('Withdrawal request cancelled by %s.') % self.env.user.name
            )
    
    def action_reset_to_draft(self):
        """Reset withdrawal to draft"""
        for record in self:
            if record.state not in ['rejected', 'cancelled']:
                raise ValidationError(_('Only rejected or cancelled withdrawals can be reset to draft.'))
            
            record.write({
                'state': 'draft',
                'rejection_reason': False,
                'rejected_by': False,
            })
            record.message_post(
                body=_('Withdrawal request reset to draft by %s.') % self.env.user.name
            )
