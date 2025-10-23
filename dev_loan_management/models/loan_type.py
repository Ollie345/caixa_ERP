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


class dev_loan_type(models.Model):
    _name = "dev.loan.type"
    _description = "Loan Type"
    
    name = fields.Char('Name', required="1", copy=False)
    is_interest_apply = fields.Boolean('Apply Interest')
    interest_mode = fields.Selection([('flat','Flat'),('reducing','Reducing')], string='Interest Mode')
    rate = fields.Float('Rate', required="1")
    proof_ids = fields.Many2many('dev.loan.proof', string='Loan Proof', required="1")
    loan_amount = fields.Float('Loan Amount Limit', required="1")
    loan_term_by_month = fields.Integer('Loan Term By Month', required="1")
    
    loan_account_id = fields.Many2one('account.account', string='Disburse Account', required="1")
    interest_account_id = fields.Many2one('account.account', string='Interest Account', required="1")
    installment_account_id = fields.Many2one('account.account', string='Installment Account', required="1")
    disburse_journal_id = fields.Many2one('account.journal', string='Disburse Journal', required="1")
    loan_payment_journal_id = fields.Many2one('account.journal', string='Payment Journal', required="1")
    none_interest_month = fields.Integer('None Interest Month')
    borrower_category_ids = fields.Many2many('borrower.category',string="Borrower Category", required="1")
    processing_fees_product_id = fields.Many2one('product.product', string='Processing Fee')
    is_required_documents = fields.Boolean('Required Documents')
    
    color = fields.Char(string="Color", help="Specify a color in hex format (e.g., #FF5733),This color will add as a background color when loan request created")
    reminder_count = fields.Integer(string="Number of Reminders")
    reminder_days = fields.Many2many('reminder.days', string="Reminder Before Days")
    image = fields.Binary(string="Image")
    eligibility_ids = fields.Many2many('dev.loan.eligibility')
    processing_fee = fields.Text('Processing Fees')
    
    
    @api.constrains('reminder_count', 'reminder_days')
    def _check_reminder_days_count(self):
        for record in self:
            if record.reminder_count >= 0 and len(record.reminder_days) != record.reminder_count:
                raise ValidationError(_(f"Please select exactly {record.reminder_count} day(s) in the Reminder Days field."))
    
    @api.onchange('is_interest_apply')
    def onchange_is_interest_apply(self):
        if self.is_interest_apply:
            self.interest_mode = 'flat'
        else:
            self.interest_mode = False
    
    @api.constrains('rate','loan_amount','loan_term_by_month')        
    def check_rate(self):
        if self.is_interest_apply and self.rate <= 0:
            raise ValidationError(_("Interest Rate Must be Positive !!!"))
        
        if self.loan_amount <= 0:
            raise ValidationError(_("Loan Amount Must be Positive !!!"))
        
        if self.loan_term_by_month <= 0:
            raise ValidationError(_("Loan Term By Month Must be Positive !!!"))
            
                

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
