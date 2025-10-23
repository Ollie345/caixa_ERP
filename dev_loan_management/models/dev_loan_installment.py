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


class dev_loan_installment(models.Model):
    _name = "dev.loan.installment"
    _order = 'loan_id desc, date'
    _description = "Installment"
    
    
    name = fields.Char('Name')
    client_id = fields.Many2one('res.partner',string='Borrower')
    loan_id = fields.Many2one('dev.loan.loan',string='Loan',required="1", ondelete='cascade')
    date = fields.Date('Date')
    state = fields.Selection([('unpaid','Unpaid'),('paid','Paid')], string='Status', default='unpaid')
    opening_balance = fields.Float('Opening')
    amount = fields.Monetary('Principal Amount', compute='_get_amount')
    interest = fields.Monetary('Interest Amount', compute='_get_interest')
    closing_balance = fields.Float('Closing')
    total_amount = fields.Monetary('EMI')
    interest_account_id = fields.Many2one('account.account', string='Interest Account')
    installment_account_id = fields.Many2one('account.account', string='Installment Account')
    loan_payment_journal_id = fields.Many2one('account.journal', string='Payment Journal')
    journal_entry_id = fields.Many2one('account.move', string='Journal Entry', copy=False)
    payment_date = fields.Date('Payment Date')
    loan_state = fields.Selection(related='loan_id.state', string='Loan State')
    is_last_line = fields.Boolean('Last Line')
    none_interest = fields.Boolean('None Interest')
    paid_interest = fields.Float('Paid Interest')
    
    company_id = fields.Many2one('res.company', string='Company', default=lambda self:self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self:self.env.user.company_id.currency_id.id)
    
    mobile = fields.Char(string="Mobile",related="client_id.mobile",readonly=False)
    email = fields.Char(string="Email",related="client_id.email",readonly=False)

    def send_by_mail(self):
        self.ensure_one()
        template_id = self.env.ref('dev_loan_management.template_overdue_installment_send_by_mail')
        ctx = {
            'default_model': 'dev.loan.installment',
            'default_res_ids': self.ids,
            'default_template_id': template_id and template_id.id or False,
            'default_composition_mode': 'comment',
            'force_email': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
    
    def action_open_installment_form(self):
        """Opens the form view of the active installment record."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Installment Form',
            'res_model': 'dev.loan.installment',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',  # Opens in the same window
        }
        
    def action_view_journal_entry(self):
        if self.journal_entry_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Journal Entry',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': self.journal_entry_id.id,
                'target': 'current',
            }
    
    
    @api.depends('total_amount','interest','is_last_line','opening_balance')
    def _get_amount(self):
        for ins in self:
            if ins.opening_balance < ins.loan_id.emi_estimate:
                ins.amount = ins.opening_balance
            else:
                if not ins.is_last_line:
                    ins.amount = ins.total_amount - ins.interest
                else:
                    ins.amount = ins.opening_balance - ins.interest
                    
    
    @api.depends('opening_balance','none_interest')
    def _get_interest(self):
        for ins in self:
            if ins.loan_id.interest_mode != 'flat':
                if ins.opening_balance and not ins.none_interest:
                    if ins.state != 'paid':
                        ins.interest = (ins.opening_balance * (ins.loan_id.interest_rate / 100))/12
                    else:
                        ins.interest = ins.paid_interest
                else:
                    ins.interest = 0
            else:
                loan_id = ins.loan_id
                if ins.state != 'paid':
                    ins.interest = ((loan_id.loan_amount * (loan_id.interest_rate / 100)) / 12)
                else:
                    ins.interest = ins.paid_interest
                
    
    def loan_installment_reminder(self):
        mtp = self.env['mail.template']
        ir_model_data = self.env['ir.model.data']
        
        # Get the email template
        template_id = ir_model_data._xmlid_lookup('dev_loan_management.installment_reminder_email_template')[1]
        template_id = mtp.browse(template_id)
        
        # Iterate through all unpaid installments and send reminders based on Loan Type configuration
        installment_ids = self.search([('state', '=', 'unpaid'), ('loan_id.state', '=', 'open')])
        
        for installment in installment_ids:
            loan_type = installment.loan_id.loan_type_id
            
            if loan_type and loan_type.reminder_days:
                # Assume reminder_days is a Many2many field and contains a list of records with `days_before_due` field
                reminder_days = [reminder.days_before_due for reminder in loan_type.reminder_days]
                due_date = installment.date
            
                for day in reminder_days:
                    reminder_date = due_date - relativedelta(days=day)
                    
                    # Check if the reminder date matches today's date
                    if reminder_date == datetime.today().date():
                        # Send reminder email
                        template_id.send_mail(installment.id, force_send=True)
            
            
        
    def get_account_move_vals(self):
        vals={
            'date':date.today(),
            'ref':self.name or 'Loan Installment',
            'journal_id':self.loan_payment_journal_id and self.loan_payment_journal_id.id or False,
            'company_id':self.loan_payment_journal_id and self.loan_payment_journal_id.company_id and self.loan_payment_journal_id.company_id.id or False,
        }
        return vals
    
    
    def get_partner_lines(self):
        vals={
            'partner_id':self.client_id and self.client_id.id or False,
            'account_id':self.client_id.property_account_receivable_id and self.client_id.property_account_receivable_id.id or False,
            'credit':self.total_amount,
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
        
        
    def set_loan_close(self):
        if self.loan_id.remaing_amount <= 0:
            self.loan_id.state = 'close'

    def unlink(self):
        for installment in self:
            if installment.loan_id.state not in ['cancel','reject'] and not installment._context.get('force_delete'):
                raise ValidationError(_('You can not delete Loan Installment.'))
        return super(dev_loan_installment, self).unlink()
        
        
    def check_unpaid_installment(self):
        date = self.date
        installment_ids = self.env['dev.loan.installment'].search([('loan_id','=',self.loan_id.id),('date','<',date),('state','=','unpaid')])
        if installment_ids:
            raise ValidationError(_("Please Pay First Before this month installment !!!"))
    
    def action_paid_installment(self):
        self.check_unpaid_installment()
        if self.loan_id and self.loan_id.state != 'open':
            raise ValidationError(_("Installment pay after loan Open !!!"))
            
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
            self.paid_interest = self.interest
            val = self.get_partner_lines()
            vals.append((0,0,val))
            if self.amount:
                val = self.get_installment_lines()
                vals.append((0,0,val))
            if self.interest:
                val = self.get_interest_lines()
                vals.append((0,0,val))
            account_move_id.line_ids = vals
            self.journal_entry_id = account_move_id and account_move_id.id or False
            self.state = 'paid'
            self.payment_date = date.today()
            self.set_loan_close()
            
    
        
            
            


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
