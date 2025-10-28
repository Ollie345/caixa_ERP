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
from odoo.exceptions import ValidationError
from datetime import datetime,date
from dateutil.relativedelta import relativedelta


class dev_advance_payment(models.Model):
    _name = "dev.advance.payment"
    _description = 'Advance Payment'
    _order = 'name desc'
    
    name = fields.Char('Name', default="/")
    client_id = fields.Many2one('res.partner',string='Borrower')
    loan_id = fields.Many2one('dev.loan.loan',string='Loan',required="1", ondelete='cascade')
    date = fields.Date('Date')
    payment_date = fields.Date('Payment Date')
    state = fields.Selection([('unpaid','Unpaid'),('paid','Paid')], string='State', default='unpaid')
    interest_account_id = fields.Many2one('account.account', string='Interest Account')
    installment_account_id = fields.Many2one('account.account', string='Installment Account')
    loan_payment_journal_id = fields.Many2one('account.journal', string='Payment Journal')
    journal_entry_id = fields.Many2one('account.move', string='Journal Entry', copy=False)
    company_id = fields.Many2one('res.company', string='Company')
    currency_id = fields.Many2one('res.currency', string='Currency')
    amount = fields.Monetary('Principal Amount', required="1")
    interest = fields.Monetary('Interest', required="1")
    paid_amount = fields.Monetary('Paid Amount', compute='_get_paid_amount')
    
    
    def get_account_move_vals(self):
        vals={
            'date':date.today(),
            'ref':self.name or 'Loan Installment',
            'journal_id':self.loan_payment_journal_id and self.loan_payment_journal_id.id or False,
            'company_id':self.company_id and self.company_id.id or False,
        }
        return vals
        
    def get_partner_lines(self):
        vals={
            'partner_id':self.client_id and self.client_id.id or False,
            'account_id':self.client_id.property_account_receivable_id and self.client_id.property_account_receivable_id.id or False,
            'credit':self.paid_amount,
            'name':self.name or '/',
            'date_maturity':date.today(),
        }
        return vals
    
    def get_installment_lines(self):
        vals={
            'partner_id':self.client_id and self.client_id.id or False,
            'account_id':self.installment_account_id and self.installment_account_id.id or False,
            'debit':self.amount,
            'name':self.name or '/',
            'date_maturity':date.today(),
        }
        return vals
    
    
    def get_interest_lines(self):
        vals={
            'partner_id':self.client_id and self.client_id.id or False,
            'account_id':self.interest_account_id and self.interest_account_id.id or False,
            'debit':self.interest,
            'name':self.name or '/',
            'date_maturity':date.today(),
        }
        return vals
        
    
    def action_pay_advance_payment(self):
        if self.loan_id and self.loan_id.state != 'open':
            raise ValidationError(_("Advance Payment Process for Open Loan !!!"))
            
        if not self.loan_payment_journal_id:
            raise ValidationError(_("Please Select Payment Journal !!!"))
            
        if not self.interest_account_id:
            raise ValidationError(_("Please Select Interest Account !!!"))
        
        if not self.installment_account_id:
            raise ValidationError(_("Please Select Installment Account !!!"))
        
        if self.client_id and not self.client_id.property_account_receivable_id:
            raise ValidationError(_("Select Client Receivable Account !!!"))
        account_move_val = self.get_account_move_vals()
        account_move_id = self.env['account.move'].create(account_move_val)
        vals=[]
        if account_move_id:
            val = self.get_partner_lines()
            vals.append((0,0,val))
            val = self.get_installment_lines()
            vals.append((0,0,val))
            if self.interest > 0:
                val = self.get_interest_lines()
                vals.append((0,0,val))
            account_move_id.line_ids = vals
            self.journal_entry_id = account_move_id and account_move_id.id or False
            self.state = 'paid'
            self.payment_date = date.today()
        
        if self.paid_amount > 0:
            installment_pool = self.env['dev.loan.installment']
            installment_ids = installment_pool.search([('loan_id','=',self.loan_id.id),('state','!=','paid')], order='date')
            set_open_balance = False
            open_balance = 0
            for ins in installment_ids:
                if not set_open_balance:
                    open_balance = ins.opening_balance - self.amount
                    set_open_balance = True
                
                if open_balance <= 0:
                    ins.total_amount = 0
                    ins.write({
                        'opening_balance':0,
                        'closing_balance':0,
                    })
                    open_balance = 0
                else:
                    ins.write({
                        'opening_balance':open_balance,
                        'closing_balance':open_balance - ins.amount,
                    })
                    if ins.closing_balance < 0:
                        ins.closing_balance = 0
                        ins.total_amount = ins.amount + ins.interest
                    open_balance = ins.closing_balance
                    
                
        return True
    
    
    
    @api.model
    def create(self,vals):
        vals.update({
                    'name':self.env['ir.sequence'].next_by_code('dev.advance.payment') or '/'
                })
        return super(dev_advance_payment,self).create(vals)
        
        
    @api.depends('amount','interest')
    def _get_paid_amount(self):
        for payment in self:
            payment.paid_amount = payment.amount + payment.interest
            
            



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
