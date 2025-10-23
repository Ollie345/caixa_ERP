# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import api, fields, models, _
from datetime import datetime
import calendar
import itertools
from operator import itemgetter
import operator
from odoo.exceptions import ValidationError
import calendar

class dev_add_advance_payment(models.TransientModel):
    _name = "dev.add.advance.payment"
    _description = 'Add Advance Payment'
    
    @api.model
    def _get_last_paid_date(self):
        loan_id = self.env['dev.loan.loan'].browse(self._context.get('default_loan_id'))
        if loan_id:
            installment_id = self.env['dev.loan.installment'].search([('state','=','paid'),('loan_id','=',loan_id.id)], order='date desc', limit=1)
            if installment_id:
                return installment_id.date
        
    
    loan_id = fields.Many2one('dev.loan.loan', string='Loan')
    date =  fields.Date('Date', required="1", default=fields.Date.today())
    amount = fields.Float('Amount', compute='_get_amount')
    interest = fields.Float('Interest', compute='_get_interest')
    paid_amount = fields.Float('Paid Amount', required="1")
    
    
    @api.depends('loan_id','date')
    def _get_interest(self):
        install_pool = self.env['dev.loan.installment']
        for payment in self:
            payment.interest = 0
            last_payment_date = False 
            current_month_days = False
            i_amount = False
            if payment.date and payment.loan_id:
                installment_id = install_pool.search([('state','=','paid'),('loan_id','=',payment.loan_id.id)], order='date desc', limit=1)
                if installment_id:
                    last_payment_date = installment_id.date
                
                current_month_days = calendar.monthrange(payment.date.year, payment.date.month)[1]
                
                if not last_payment_date:
                    last_payment_date = payment.loan_id.disbursement_date
                    
                if last_payment_date >= payment.date:
                    payment.interest = 0
                else:
                    diff_days = (payment.date - last_payment_date).days
                    installment_id = install_pool.search([('state','!=','paid'),('loan_id','=',payment.loan_id.id)], order='date', limit=1)
                    if installment_id:
                        i_amount = installment_id.interest
                    if i_amount and current_month_days  and diff_days > 0:
                        payment.interest = i_amount * diff_days / current_month_days
                
            
            
    @api.depends('paid_amount','interest')
    def _get_amount(self):
        for payment in self:
            payment.amount = payment.paid_amount - payment.interest
    
    
    def action_add_payment(self):
        if self.paid_amount <= 0:
            raise ValidationError(_('Paid Amount Must be Positive'))
        
        loan_type_id = self.loan_id.loan_type_id
        vals={
            'client_id':self.loan_id.client_id and self.loan_id.client_id.id or False,
            'loan_id':self.loan_id and self.loan_id.id or False,
            'date':self.date,
            'state':'unpaid',
            'interest_account_id':loan_type_id.interest_account_id and loan_type_id.interest_account_id.id or False,
            'installment_account_id':loan_type_id.installment_account_id and loan_type_id.installment_account_id.id or False, 
            'loan_payment_journal_id':loan_type_id.loan_payment_journal_id and loan_type_id.loan_payment_journal_id.id or False,
            'company_id':self.loan_id.company_id and self.loan_id.company_id.id or False,
            'currency_id':self.loan_id.currency_id and self.loan_id.currency_id.id or False,
            'amount':self.amount or 0.0,
            'interest':self.interest or 0.0}
        self.env['dev.advance.payment'].create(vals)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
    
