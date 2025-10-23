# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class DevLoanRestructure(models.Model):
    _name = 'dev.loan.restructure'
    _description = 'Loan Restructure Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    name = fields.Char(string='Reference', readonly=True, default='/', copy=False)
    loan_id = fields.Many2one('dev.loan.loan', string='Loan', required=True, domain=[('state', 'in', ['open'])], tracking=True)
    action_type = fields.Selection([
        ('restructure', 'Restructure'),
        ('payoff', 'Pay Off'),
        ('writeoff', 'Write Off'),
    ], required=True, tracking=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today, tracking=True)

    # For restructure (new terms)
    new_amount = fields.Monetary(string='New Amount', currency_field='currency_id')
    period_months = fields.Integer(string='Period (Months)')
    interest_rate = fields.Float(string='Interest Rate (%)')
    new_schedule_ids = fields.One2many('dev.loan.restructure.line', 'restructure_id', string='New Schedule')

    # For payoff/writeoff (settlement)
    settlement_account_id = fields.Many2one(
        'account.account',
        string='Settlement Account',
        domain="[('account_type', 'in', ['asset_cash','liability_credit_card','liability_current','expense'])]"
    )
    note = fields.Text(string='Notes')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending_cfo', 'Pending CFO'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft', required=True, tracking=True)

    treasurer_id = fields.Many2one('res.users', string='Treasurer', readonly=True, tracking=True)
    cfo_id = fields.Many2one('res.users', string='CFO', readonly=True, tracking=True)
    approval_date = fields.Date(string='Approval Date', readonly=True, tracking=True)

    company_id = fields.Many2one(related='loan_id.company_id', store=True)
    currency_id = fields.Many2one(related='loan_id.currency_id', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('dev.loan.restructure') or '/'
        return super().create(vals_list)

    # Permissions: Treasurer = group_loan_user, CFO = group_loan_manager
    def _check_submit_perm(self):
        if not self.env.user.has_group('dev_loan_management.group_loan_user'):
            raise UserError(_("You don't have permission to submit this request."))

    def _check_approve_perm(self):
        if not self.env.user.has_group('dev_loan_management.group_loan_manager'):
            raise UserError(_("You don't have permission to approve this request."))

    def action_submit_for_approval(self):
        self.ensure_one()
        self._validate_submission()
        self._check_submit_perm()
        self.write({
            'state': 'pending_cfo',
            'treasurer_id': self.env.user.id,
        })
        return True

    def action_approve(self):
        self.ensure_one()
        self._check_approve_perm()
        self.write({
            'state': 'approved',
            'cfo_id': self.env.user.id,
            'approval_date': fields.Date.today(),
        })
        if self.action_type == 'restructure':
            self._execute_restructure_action()
        elif self.action_type == 'payoff':
            self._execute_payoff_action()
        elif self.action_type == 'writeoff':
            self._execute_writeoff_action()
        return True

    def action_reject(self):
        self.ensure_one()
        self._check_approve_perm()
        self.write({
            'state': 'rejected',
            'cfo_id': self.env.user.id,
            'approval_date': fields.Date.today(),
        })
        return True

    def _validate_submission(self):
        self.ensure_one()
        if self.action_type == 'restructure':
            if not (self.new_amount and self.period_months and self.interest_rate is not None):
                raise UserError(_("Please set new amount, period, and interest rate for restructure."))
        else:
            if not self.settlement_account_id:
                raise UserError(_("Please select a settlement account for payoff/writeoff."))

    def _execute_restructure_action(self):
        loan = self.loan_id
        # Delete existing schedule and regenerate from new terms
        loan.installment_ids.with_context(force_delete=True).unlink()
        loan.write({
            'loan_amount': self.new_amount,
            'loan_term': self.period_months,
            'interest_rate': self.interest_rate,
        })
        # Recompute schedule from the restructure date
        loan.compute_installment(self.date)
        self.message_post(body=_("Loan restructured. New terms applied and schedule regenerated."))

    def _execute_payoff_action(self):
        loan = self.loan_id
        outstanding = loan.remaing_amount
        if outstanding <= 0:
            raise UserError(_("No outstanding balance to pay off."))

        # Single JE to settle receivable
        move = self.env['account.move'].create({
            'date': self.date,
            'ref': f'Loan Payoff {loan.name} - {self.name}',
            'journal_id': loan.disburse_journal_id.id or (loan.loan_type_id and loan.loan_type_id.loan_payment_journal_id.id),
            'line_ids': [
                (0, 0, {
                    'partner_id': loan.client_id.id,
                    'account_id': self.settlement_account_id.id,  # Bank/Cash
                    'debit': outstanding,
                    'credit': 0.0,
                    'name': f'Loan payoff - {loan.name}',
                }),
                (0, 0, {
                    'partner_id': loan.client_id.id,
                    'account_id': loan.client_id.property_account_receivable_id.id,  # AR
                    'debit': 0.0,
                    'credit': outstanding,
                    'name': f'Loan payoff - {loan.name}',
                }),
            ],
        })
        move.action_post()

        # Close loan: drop remaining unpaid installments
        loan.installment_ids.filtered(lambda i: i.state == 'unpaid').with_context(force_delete=True).unlink()
        loan.state = 'close'
        self.message_post(body=_("Loan payoff completed. Journal entry posted and loan closed."))

    def _execute_writeoff_action(self):
        loan = self.loan_id
        outstanding = loan.remaing_amount
        if outstanding <= 0:
            raise UserError(_("No outstanding balance to write off."))

        # Write-off (we are the lender): Expense debit, AR credit
        move = self.env['account.move'].create({
            'date': self.date,
            'ref': f'Loan Write-off {loan.name} - {self.name}',
            'journal_id': loan.disburse_journal_id.id or (loan.loan_type_id and loan.loan_type_id.loan_payment_journal_id.id),
            'line_ids': [
                (0, 0, {
                    'partner_id': loan.client_id.id,
                    'account_id': self.settlement_account_id.id,  # Bad debt expense
                    'debit': outstanding,
                    'credit': 0.0,
                    'name': f'Loan write-off - {loan.name}',
                }),
                (0, 0, {
                    'partner_id': loan.client_id.id,
                    'account_id': loan.client_id.property_account_receivable_id.id,  # AR
                    'debit': 0.0,
                    'credit': outstanding,
                    'name': f'Loan write-off - {loan.name}',
                }),
            ],
        })
        move.action_post()

        loan.installment_ids.filtered(lambda i: i.state == 'unpaid').with_context(force_delete=True).unlink()
        loan.state = 'close'
        self.message_post(body=_("Loan write-off completed. Journal entry posted and loan closed."))


