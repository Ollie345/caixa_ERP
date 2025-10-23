# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class DevLoanRestructureWizard(models.TransientModel):
    _name = 'dev.loan.restructure.wizard'
    _description = 'Loan Restructure Wizard'

    loan_id = fields.Many2one('dev.loan.loan', string='Loan', required=True, domain=[('state', '=', 'open')])
    action_type = fields.Selection([
        ('restructure', 'Restructure'),
        ('payoff', 'Pay Off'),
        ('writeoff', 'Write Off'),
    ], required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)

    # Restructure terms
    new_amount = fields.Monetary(string='New Amount', currency_field='currency_id')
    period_months = fields.Integer(string='Period (Months)')
    interest_rate = fields.Float(string='Interest Rate (%)')
    generate_schedule = fields.Boolean(string='Generate New Schedule', default=True)

    # Settlement
    settlement_account_id = fields.Many2one(
        'account.account',
        string='Settlement Account',
        domain="[('account_type', 'in', ['asset_cash','liability_credit_card','liability_current','expense'])]"
    )
    note = fields.Text(string='Notes')

    currency_id = fields.Many2one(related='loan_id.currency_id', store=False)

    def action_create_request(self):
        self.ensure_one()
        vals = {
            'loan_id': self.loan_id.id,
            'action_type': self.action_type,
            'date': self.date,
            'note': self.note,
        }
        if self.action_type == 'restructure':
            if not (self.new_amount and self.period_months and self.interest_rate is not None):
                raise UserError(_("Please set new amount, period, and interest rate."))
            vals.update({
                'new_amount': self.new_amount,
                'period_months': self.period_months,
                'interest_rate': self.interest_rate,
            })
        else:
            if not self.settlement_account_id:
                raise UserError(_("Settlement account is required."))
            vals['settlement_account_id'] = self.settlement_account_id.id

        req = self.env['dev.loan.restructure'].create(vals)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dev.loan.restructure',
            'res_id': req.id,
            'view_mode': 'form',
            'target': 'current',
        }


