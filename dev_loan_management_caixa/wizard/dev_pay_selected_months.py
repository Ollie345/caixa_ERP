# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date

class dev_pay_selected_months(models.TransientModel):
    _name = "dev.pay.selected.months"
    _description = 'Pay Selected Months'

    loan_id = fields.Many2one(
        'dev.loan.loan',
        string='Loan',
        required=True,
        readonly=True,
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='loan_id.currency_id',
        readonly=True,
    )
    
    installment_ids = fields.Many2many(
        'dev.loan.installment',
        'dev_pay_selected_months_installment_rel',
        'wizard_id',
        'installment_id',
        string='Select Installments',
        domain="[('loan_id', '=', loan_id), ('state', '=', 'unpaid')]",
        required=True,
    )
    
    payment_date = fields.Date(
        string='Payment Date',
        default=fields.Date.today,
        required=True,
    )
    
    # Computed totals
    total_principal = fields.Monetary(
        string='Total Principal',
        compute='_compute_totals',
        store=False,
    )
    
    total_interest = fields.Monetary(
        string='Total Interest',
        compute='_compute_totals',
        store=False,
    )
    
    total_penalty = fields.Monetary(
        string='Total Penalty',
        compute='_compute_totals',
        store=False,
    )
    
    total_amount = fields.Monetary(
        string='Total Amount',
        compute='_compute_totals',
        store=False,
    )
    
    @api.depends('installment_ids')
    def _compute_totals(self):
        """Calculate totals for selected installments"""
        for wizard in self:
            if wizard.installment_ids:
                wizard.total_principal = sum(wizard.installment_ids.mapped('amount') or [0.0])
                wizard.total_interest = sum(wizard.installment_ids.mapped('interest') or [0.0])
                wizard.total_penalty = sum(wizard.installment_ids.mapped('penalty_amount') or [0.0])
                wizard.total_amount = wizard.total_principal + wizard.total_interest + wizard.total_penalty
            else:
                wizard.total_principal = 0.0
                wizard.total_interest = 0.0
                wizard.total_penalty = 0.0
                wizard.total_amount = 0.0
    
    def _validate_payment(self):
        """Validate payment prerequisites"""
        if not self.installment_ids:
            raise ValidationError(_("Please select at least one installment to pay."))
        
        if self.loan_id.state != 'open':
            raise ValidationError(_("Loan must be open to process payments."))
        
        # Check if installments belong to the loan
        for inst in self.installment_ids:
            if inst.loan_id.id != self.loan_id.id:
                raise ValidationError(_("All selected installments must belong to the same loan."))
            
            if inst.state == 'paid':
                raise ValidationError(_("One or more selected installments are already paid."))
        
        # Validate accounts and journal
        loan_type = self.loan_id.loan_type_id
        if not loan_type.loan_payment_journal_id:
            raise ValidationError(_("Please configure Payment Journal in Loan Type."))
        
        if not loan_type.installment_account_id:
            raise ValidationError(_("Please configure Installment Account in Loan Type."))
        
        if not loan_type.interest_account_id:
            raise ValidationError(_("Please configure Interest Account in Loan Type."))
        
        if not self.loan_id.client_id.property_account_receivable_id:
            raise ValidationError(_("Please configure Receivable Account for the borrower."))
    
    def action_pay_selected_months(self):
        """Process payment for selected installments using single journal entry"""
        self.ensure_one()
        
        # Validate payment
        self._validate_payment()
        
        loan = self.loan_id
        loan_type = loan.loan_type_id
        
        # Sort installments by date to process sequentially
        sorted_installments = self.installment_ids.sorted('date')
        
        # Calculate totals
        total_principal = sum(sorted_installments.mapped('amount') or [0.0])
        total_interest = sum(sorted_installments.mapped('interest') or [0.0])
        total_penalty = sum(sorted_installments.mapped('penalty_amount') or [0.0])
        total_amount = total_principal + total_interest + total_penalty
        
        if total_amount <= 0:
            raise ValidationError(_("Total amount must be greater than zero."))
        
        # Create journal entry
        move = self.env['account.move'].create({
            'journal_id': loan_type.loan_payment_journal_id.id,
            'date': self.payment_date,
            'ref': f"Bulk Payment - {loan.name} ({len(sorted_installments)} installments)",
            'company_id': loan.company_id.id if loan.company_id else False,
        })
        
        # Prepare journal lines
        lines = []
        
        # Partner line (Credit - receiving payment from borrower)
        lines.append((0, 0, {
            'partner_id': loan.client_id.id,
            'account_id': loan.client_id.property_account_receivable_id.id,
            'credit': total_amount,
            'debit': 0.0,
            'name': f"Payment for {len(sorted_installments)} installments - {loan.name}",
            'date_maturity': self.payment_date,
        }))
        
        # Principal line (Debit)
        if total_principal > 0:
            lines.append((0, 0, {
                'partner_id': loan.client_id.id,
                'account_id': loan_type.installment_account_id.id,
                'debit': total_principal,
                'credit': 0.0,
                'name': f'Principal Payment - {loan.name}',
                'date_maturity': self.payment_date,
            }))
        
        # Interest line (Debit)
        if total_interest > 0:
            lines.append((0, 0, {
                'partner_id': loan.client_id.id,
                'account_id': loan_type.interest_account_id.id,
                'debit': total_interest,
                'credit': 0.0,
                'name': f'Interest Payment - {loan.name}',
                'date_maturity': self.payment_date,
            }))
        
        # Penalty line (Debit) - if penalty exists
        if total_penalty > 0:
            # Use interest account for penalty (or create separate penalty account if needed)
            penalty_account = loan_type.interest_account_id.id
            lines.append((0, 0, {
                'partner_id': loan.client_id.id,
                'account_id': penalty_account,
                'debit': total_penalty,
                'credit': 0.0,
                'name': f'Penalty Payment - {loan.name}',
                'date_maturity': self.payment_date,
            }))
        
        # Set journal lines
        move.line_ids = lines
        
        # Post the journal entry
        move.action_post()
        
        # Mark installments as paid and update balances
        self._mark_installments_paid(sorted_installments, move)
        
        # Check if loan should be closed
        remaining_unpaid = loan.installment_ids.filtered(lambda i: i.state != 'paid')
        if not remaining_unpaid:
            loan.write({'state': 'close'})
        
        return {
            'type': 'ir.actions.act_window_close'
        }
    
    def _mark_installments_paid(self, sorted_installments, move):
        """Mark selected installments as paid and update balances"""
        loan = self.loan_id
        
        # Get current opening balance (from last paid installment)
        last_paid_installments = loan.installment_ids.filtered(
            lambda i: i.state == 'paid'
        ).sorted('date')
        
        # Start with opening balance from last paid installment or loan amount
        if last_paid_installments:
            opening_balance = last_paid_installments[-1].closing_balance
        else:
            opening_balance = loan.loan_amount
        
        # Process each selected installment sequentially
        for inst in sorted_installments:
            # Calculate closing balance
            closing_balance = opening_balance - inst.amount
            if closing_balance < 0:
                closing_balance = 0.0
            
            # Update installment
            inst.write({
                'state': 'paid',
                'payment_date': self.payment_date,
                'journal_entry_id': move.id,
                'paid_interest': inst.interest,
                'opening_balance': opening_balance,
                'closing_balance': closing_balance,
            })
            
            # Update opening balance for next installment
            opening_balance = closing_balance
        
        # Update remaining unpaid installments' opening balances
        remaining_unpaid = loan.installment_ids.filtered(
            lambda i: i.state == 'unpaid' and i.date > sorted_installments[-1].date
        ).sorted('date')
        
        for inst in remaining_unpaid:
            closing_balance = opening_balance - inst.amount
            if closing_balance < 0:
                closing_balance = 0.0
            
            inst.write({
                'opening_balance': opening_balance,
                'closing_balance': closing_balance,
            })
            
            opening_balance = closing_balance
        
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

