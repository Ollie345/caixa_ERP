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
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import RedirectWarning


class dev_loan_loan(models.Model):
    _name = "dev.loan.loan"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _description = "Loan"
    
    name = fields.Char('Name', default='/', copy=False)
    client_id = fields.Many2one('res.partner', domain=[('is_allow_loan','=',True)], required="1", string='Borrower')
    request_date =fields.Date('Request Date', default=fields.Date.today(), required="1")
    approve_date = fields.Date('Approve Date', copy=False)
    disbursement_date = fields.Date('Disbursement Date', copy=False)
    loan_type_id = fields.Many2one('dev.loan.type', string='Loan Type', required="1")
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    loan_amount = fields.Monetary('Loan Amount', required="1")
    loan_purpose = fields.Char('Loan Purpose')
    collateral = fields.Char('Collateral')
    source_of_repayment = fields.Char('Source of Repayment')
    is_interest_apply = fields.Boolean(related='loan_type_id.is_interest_apply', string='Apply Interest')
    interest_rate = fields.Float(string='Interest Rate')
    none_interest_month = fields.Integer(string='None Interest Month')
    loan_term = fields.Integer('Loan Term', required="1")
    interest_mode = fields.Selection(related='loan_type_id.interest_mode', string='Interest Mode')	
    
    state = fields.Selection([('draft','Draft'),
                              ('confirm','Confirm'),
                              ('review','Reviewed'),
                              ('approve','Approve'),
                              ('disburse','Disburse'),
                              ('open','Open'),
                              ('close','Close'),
                              ('cancel','Cancel'),
                              ('reject','Reject')], string='Status', required="1", default='draft',tracking=1)
    
    
    installment_ids = fields.One2many('dev.loan.installment','loan_id', string='Installments')
    
    total_interest = fields.Monetary('Interest Amount', compute='get_total_interest')
    paid_amount = fields.Monetary('Paid Amount', compute='get_total_interest')
    remaing_amount = fields.Monetary('Remaining Amount', compute='get_total_interest')
    total_estimated_paid_amount = fields.Monetary('Total Estimated Amount To Pay', compute='get_total_estimated_paid_amount')
    notes = fields.Text('Notes')
    reject_reason = fields.Text('Reject Reason', copy=False)
    reject_user_id = fields.Many2one('res.users','Reject By', copy=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self:self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self:self.env.user.company_id.currency_id.id)
    proof_ids = fields.Many2many('dev.loan.proof', string='Loan Proof') 
    loan_account_id = fields.Many2one('account.account', string='Disburse Account')
    disburse_journal_id = fields.Many2one('account.journal', string='Disburse Journal')
    disburse_journal_entry_id = fields.Many2one('account.move', string='Disburse Account Entry', copy=False)
    loan_document_ids = fields.One2many('ir.attachment','res_id', string='Loan Document',
                                            domain=[('document_type','=','loan')],
                                            context={
                                            'default_res_model': 'dev.loan.loan',
                                            'default_res_id': lambda self: self.id,
                                            'default_document_type': 'loan',
                                        })
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments')
    emi_estimate = fields.Monetary(string="Estimated Monthly Payment", compute="_estimated_monthly_payment")
    adv_payment_lines = fields.One2many('dev.advance.payment','loan_id', string='Advance Payment')
    count_installment = fields.Integer('Count Installment', compute='_get_count_installment')
    color = fields.Integer(string='Color')
    domain_loan_type_ids = fields.Many2many('dev.loan.type', string="Available Loan Types", compute="_compute_domain_loan_type_ids")
    processing_fee = fields.Boolean(string="Processing Fees")
    fee_type = fields.Selection(string="Fees Type",selection=[('fixed','Fixed'),('percentage','Percentage')],default='fixed')
    processing_fixed_amount = fields.Monetary('Fixed Amount')
    processing_percentage = fields.Float('Percentage')
    invoice_count = fields.Integer('Invoice Count', compute='_compute_invoice_count')
    witness_ids=fields.One2many('ln.witness','loan_id',string='Witness')
    checklist_line_ids = fields.One2many('checklist.line','loan_id',string="Checklist Line")
    percentage = fields.Integer(compute = 'compute_percentage')
    loan_checklist_template_id = fields.Many2one('loan.checklist.template', string='Checklist', copy=False)
    restructure_ids = fields.One2many('dev.loan.restructure','loan_id', string='Restructure History', readonly=True)
    
    co_borrower=fields.Boolean(string='Co-Borrower')
    co_borrower_ids=fields.One2many('ln.co.borrower','loan_id',string='Co-Borrower')
    co_borrower_document_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        string='Co-Borrower Document',
        domain=[('document_type','=','co_borrower')],
        context={
            'default_res_model': 'dev.loan.loan',
            'default_res_id': lambda self: self.id,  # Ensures attachments link to the current record
            'default_document_type': 'co_borrower', 
        }
    )
    loan_agreement = fields.Integer(string='Agreement ',compute='compute_loan_agreement_count')
    
    loan_type_color = fields.Char(string="Loan Type Color", related='loan_type_id.color')
    next_installment_date = fields.Date(string="Next Installment Date",compute="_compute_next_installment_date")
    lead_id = fields.Many2one('crm.lead',string="Lead")
    task_count = fields.Integer(compute="get_task_count")
    loan_notice=fields.Integer(string='Notice',compute='compute_loan_notice_count')
    
    
    def compute_loan_notice_count(self):
       for loan in self:
            loan_ids=self.env['ln.notice'].search([('partner_id','=',self.client_id.id),('loan_id','=',self.id)])
            loan.loan_notice = len(loan_ids)  

    def view_loan_notice(self):
         loan_ids=self.env['ln.notice'].search([('partner_id','=',self.client_id.id),('loan_id','=',self.id)])
         list_id = loan_ids.ids
         action = self.env.ref('dev_loan_management.action_dev_loan_notice').sudo().read()[0]
         if len(list_id) > 1:
            action['domain'] = [('id', 'in', list_id)]
         elif len(list_id) == 1:
            action['views'] = [(self.env.ref('dev_loan_management.view_dev_loan_notice_form').id, 'form')]
            action['res_id'] = list_id[0]
         else:
            action = {'type': 'ir.actions.act_window_close'}
         return action

  
    # Task 
    def view_task_list(self):
        task_ids = self.env['project.task'].search([('loan_id', '=', self.id)])
        action = self.env["ir.actions.actions"]._for_xml_id('project.action_view_all_task')
        if len(task_ids) > 1:
            action['domain'] = [('id', 'in', task_ids.ids)]
        elif len(task_ids) == 1:
            action['views'] = [(self.env.ref('project.view_task_form2').id, 'form')]
            action['res_id'] = task_ids[0].id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

 
    def get_task_count(self):   
        for count in self:
            task_ids = self.env['project.task'].search([('loan_id', '=',count.id)])  
            count.task_count = len(task_ids)
    
    
    @api.depends('installment_ids.date', 'installment_ids.state')
    def _compute_next_installment_date(self):
        for record in self:
            # Get the current date
            current_date = fields.Date.today()
            
            # Filter installments: future date and unpaid
            future_unpaid_installments = record.installment_ids.filtered(
                lambda i: i.date and i.date > current_date and i.state == 'unpaid'
            )
            
            # Check if there are any future unpaid installments
            if future_unpaid_installments:
                # Get the earliest unpaid installment date
                next_date = min(future_unpaid_installments.mapped('date'))
                record.next_installment_date = next_date
            else:
                # No future unpaid installments
                record.next_installment_date = False
    
    #    PORTAL
    def _compute_access_url(self):
        super(dev_loan_loan, self)._compute_access_url()
        for loan in self:
            loan.access_url = '/my/loan/%s' % (loan.id)

    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % (_('Loan'), self.name)
        
        
        
    def compute_loan_agreement_count(self):
       for loan in self:
            loan_ids=self.env['ln.agreement'].search([('partner_id','=',self.client_id.id),('loan_id','=',self.id)])
            loan.loan_agreement = len(loan_ids)
       
    def view_loan_agreement(self):
         loan_ids=self.env['ln.agreement'].search([('partner_id','=',self.client_id.id),('loan_id','=',self.id)])
         list_id = loan_ids.ids
         action = self.env.ref('dev_loan_management.action_dev_loan_agreement').sudo().read()[0]
         if len(list_id) > 1:
            action['domain'] = [('id', 'in', list_id)]
         elif len(list_id) == 1:
            action['views'] = [(self.env.ref('dev_loan_management.view_dev_loan_agreement_form').id, 'form')]
            action['res_id'] = list_id[0]
         else:
            action = {'type': 'ir.actions.act_window_close'}
         return action    
        
    @api.onchange('loan_checklist_template_id')
    def onchange_loan_checklist_template_id(self):
        if self.checklist_line_ids:
            self.checklist_line_ids = False
                       
        for line in self.loan_checklist_template_id.checklist_ids:                                                         
            self.checklist_line_ids = [(0,0,
                                       {'document_id':line.id or False,
                                        'document_type_id':line.document_type_id and line.document_type_id.id or False,}  
                                      )]   
    
    def compute_percentage(self):
        for record in self:
            if record.checklist_line_ids:
                total= len(record.checklist_line_ids.ids)
                completed_records = 0
                for rec in record.checklist_line_ids:
                    if rec.state == 'done':
                        complete_total= len(rec.ids)
                        completed_records += complete_total
                percentage = completed_records / total * 100
                record.percentage = percentage
            else:
                record.percentage = 0

    def action_view_invoice(self):
        invoice_id = self.env['account.move'].search([('loan_ref_id', '=', self.id),('move_type','=','out_invoice')])
        invoice_ids = invoice_id.ids
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        if len(invoice_ids) > 1:
            action['domain'] = [('id', 'in', invoice_ids)]
        elif len(invoice_ids) == 1:
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = invoice_ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action  
        
    def _compute_invoice_count(self):
        for invoice in self:
            invoice_ids = self.env['account.move'].search([('loan_ref_id', '=', self.id),('move_type','=','out_invoice')])
            invoice.invoice_count = len(invoice_ids)
          
    @api.depends('client_id')
    def _compute_domain_loan_type_ids(self):
        for record in self:
            if record.client_id and record.client_id.borrower_category_id:
                borrower_category_id = record.client_id.borrower_category_id.id
                loan_types = self.env['dev.loan.type'].search([('borrower_category_ids', 'in', [borrower_category_id])])
                record.domain_loan_type_ids = loan_types
            else:
                record.domain_loan_type_ids = self.env['dev.loan.type']
            
    def get_account(self, product_id):
        account_id = False
        if product_id:
            account_id = product_id.property_account_income_id or False
        if not account_id:
            account_id = product_id.categ_id and product_id.categ_id.property_account_income_categ_id or False
        return account_id
            
    def create_processing_fees_invoice(self):
        if self.fee_type == 'fixed':
            if self.processing_fixed_amount <= 0:
                raise ValidationError(_('''Fixed Amount of Processing Fees is Zero or Less Then Zero, Invoice can't be generated !'''))
            loan_type_action = self.env.ref('dev_loan_management.action_dev_loan_type')
            if not self.loan_type_id.processing_fees_product_id:
                msg = _('Configure Processing Fees Product into the Loan Type !')
                raise RedirectWarning(msg, loan_type_action.id, _('Go to the Loan Type page'))
                
            processing_fees_product_id = self.loan_type_id and self.loan_type_id.processing_fees_product_id or False
            invoice_lines = []
            if self.loan_type_id.processing_fees_product_id:
                account_id = self.get_account(processing_fees_product_id)
                if not account_id:
                    raise ValidationError(_('''There is no income account defined for the product '%s' ''') % (
                        processing_fees_product_id.name))
                line_vals = {'product_id': processing_fees_product_id.id,
                             'name': self.name + ' : ' + 'Processing Fee',
                             'account_id': account_id.id,
                             'price_unit': self.processing_fixed_amount,
                             'quantity': 1,
                             'product_uom_id': processing_fees_product_id.uom_id and processing_fees_product_id.uom_id.id or False
                             }
                invoice_lines.append((0, 0, line_vals))
               
            vals = {'move_type': 'out_invoice',
                    'partner_id': self.client_id and self.client_id.id or False,
                    'loan_ref_id': self.id,
                    'invoice_date': date.today(),
                    'invoice_line_ids': invoice_lines}
            self.env['account.move'].create(vals)
            
        if self.fee_type == 'percentage':
            if self.processing_percentage <= 0:
                raise ValidationError(_('''Percentage of Processing Fees is Zero or Less Then Zero, Invoice can't be generated !'''))
            loan_type_action = self.env.ref('dev_loan_management.action_dev_loan_type')
            if not self.loan_type_id.processing_fees_product_id:
                msg = _('Configure Processing Fees Product into the Loan Type !')
                raise RedirectWarning(msg, loan_type_action.id, _('Go to the Loan Type page'))
                
            processing_fees_product_id = self.loan_type_id and self.loan_type_id.processing_fees_product_id or False
            invoice_lines = []
            if self.loan_type_id.processing_fees_product_id:
                account_id = self.get_account(processing_fees_product_id)
                if not account_id:
                    raise ValidationError(_('''There is no income account defined for the product '%s' ''') % (
                        processing_fees_product_id.name))
                amount = 0
                if self.processing_percentage:
                    amount = (self.loan_amount * self.processing_percentage / 100)
                line_vals = {'product_id': processing_fees_product_id.id,
                             'name': self.name + ' : ' + 'Processing Fee',
                             'account_id': account_id.id,
                             'price_unit': amount,
                             'quantity': 1,
                             'product_uom_id': processing_fees_product_id.uom_id and processing_fees_product_id.uom_id.id or False
                             }
                invoice_lines.append((0, 0, line_vals))
               
            vals = {'move_type': 'out_invoice',
                    'partner_id': self.client_id and self.client_id.id or False,
                    'loan_ref_id': self.id,
                    'invoice_date': date.today(),
                    'invoice_line_ids': invoice_lines}
            self.env['account.move'].create(vals)
        
    
    
    def _compute_attachment_number(self):
        for loan in self:
            loan.attachment_number = len(loan.loan_document_ids.ids + loan.co_borrower_document_ids.ids)
    
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'dev.loan.loan'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'dev.loan.loan', 'default_res_id': self.id}
        return res
        
    def action_view_installment(self):
        if self.installment_ids:
            action = self.env.ref('dev_loan_management.action_dev_loan_installment').read()[0]
            action['domain'] = [('id', 'in', self.installment_ids.ids),('state','not in',['draft','reject','cancel'])]
            action['context']= {}
            return action
        else:
            return {'type': 'ir.actions.act_window_close'}
            
            
    def unlink(self):
        for loan in self:
            if loan.state not in ['draft','cancel']:
                raise ValidationError(_('Loan delete on Draft and cancel state only !!!.'))
        return super(dev_loan_loan, self).unlink()
        
    
    @api.depends('installment_ids')
    def _get_count_installment(self):
        for loan in self:
            if loan.installment_ids:
                loan.count_installment = len(loan.installment_ids)
            else:
                loan.count_installment = 0
                
                
    
    @api.depends('interest_rate','loan_term','loan_amount')
    def _estimated_monthly_payment(self):
        for loan in self:
            loan.emi_estimate = 0.0
            if loan.interest_rate and loan.loan_amount and loan.loan_term:
                if loan.interest_mode == 'reducing':
                    if loan.interest_rate and loan.loan_term and loan.loan_amount:
                        k = 12
                        i = loan.interest_rate / 100
                        a = i / k or 0.00
                        b = (1 - (1 / ((1 + (i / k)) ** loan.loan_term))) or 0.00
                        emi = ((loan.loan_amount * a) / b) or 0.00
                        loan.emi_estimate =  emi
                else:
                    loan.emi_estimate = (loan.loan_amount / loan.loan_term) + ((loan.loan_amount * (loan.interest_rate / 100)) / 12)
                    
            if not loan.interest_rate and loan.loan_amount and loan.loan_term:
                loan.emi_estimate = (loan.loan_amount / loan.loan_term)
                    
                    
    def _make_url(self):
        ir_param = self.env['ir.config_parameter'].sudo()
        base_url = ir_param.get_param('web.base.url')
        menu_id = self.env.ref('dev_loan_management.menu_dev_loan_request_approve').id
        action_id = self.env.ref('dev_loan_management.action_dev_loan_loan_approve').id
        if base_url:
            base_url += '/web#id=%s&cids=1&menu_id=%s&action=%s&model=%s&view_type=form' % (self.id, menu_id, action_id, self._name)
        return base_url
                    
                    
    @api.depends('installment_ids')
    def get_total_interest(self):
        for loan in self:
            total_interest = 0
            paid_amount = 0
            remaing_amount = 0
            
            for adv in loan.adv_payment_lines:
                paid_amount += adv.paid_amount
                
            for installment in loan.installment_ids:
                total_interest += installment.interest
                if installment.state == 'paid':
                    paid_amount+= installment.total_amount
                else:
                    remaing_amount += installment.total_amount
            loan.total_interest = total_interest
            loan.paid_amount = paid_amount
            loan.remaing_amount = remaing_amount
            
    @api.depends('installment_ids')
    def get_total_estimated_paid_amount(self):
        for loan in self:
            total_amount = 0   
            for installment in loan.installment_ids:
                total_amount += installment.total_amount
            loan.total_estimated_paid_amount = total_amount
            
    
    @api.depends('total_interest','loan_amount')
    def get_total_amount_to_pay(self):
        for loan in self:
            loan.total_amount_to_pay = loan.total_interest + loan.loan_amount
    
    def get_loan_account_journal(self):
        interest_account_id = installment_account_id = loan_payment_journal_id = False
        if not self.loan_type_id:
            raise ValidationError(_("Please Select the Loan Type !!!"))
        if self.loan_type_id.interest_account_id:
            interest_account_id = self.loan_type_id.interest_account_id and self.loan_type_id.interest_account_id.id or False
        
        if self.loan_type_id.installment_account_id:
            installment_account_id = self.loan_type_id.installment_account_id and self.loan_type_id.installment_account_id.id or False
        
        if self.loan_type_id.loan_payment_journal_id:
            loan_payment_journal_id = self.loan_type_id.loan_payment_journal_id and self.loan_type_id.loan_payment_journal_id.id or False
            
        return interest_account_id,installment_account_id,loan_payment_journal_id
            
    
    def compute_installment(self,date=False):
        if self.installment_ids:
            for installment in self.installment_ids:
                installment.with_context({'force_delete':True}).unlink()
        opening_balance = self.loan_amount
        if self.state == 'draft':
            date = self.request_date
        else:
            date = date
        vals = []
        interest_account_id,installment_account_id,loan_payment_journal_id = self.get_loan_account_journal()
        interest =  ((self.loan_amount * (self.interest_rate / 100)) / 12)
        for i in range(1,self.loan_term+1):
            emi = float("{:.2f}".format(self.emi_estimate))
            if self.interest_mode != 'flat':
                interest = (opening_balance * (self.interest_rate / 100)) / 12
            interest = float("{:.2f}".format(interest))
            if opening_balance < emi:
                emi = opening_balance + interest
            principal = emi - interest
            closing_amount = opening_balance - principal
            date = date+relativedelta(months=1)
            none_interest = False
            if i <= self.none_interest_month:
                none_interest = True
                closing_amount = opening_balance - emi
            if closing_amount < 0.0:
                closing_amount = 0.0
            vals.append((0, 0,{
                'name':'INS - '+self.name+ ' - '+str(i),
                'client_id':self.client_id and self.client_id.id or False,
                'date':date,
                'opening_balance':opening_balance,
                'amount':principal,
                'none_interest':none_interest,
                'interest':interest,
                'closing_balance':closing_amount,
                'total_amount':float("{:.2f}".format(interest+principal)),
                'state':'unpaid',
                'interest_account_id':interest_account_id or False,
                'installment_account_id':installment_account_id or False,
                'loan_payment_journal_id':loan_payment_journal_id or False,
                'currency_id':self.currency_id and self.currency_id.id or False,
            }))
            opening_balance = closing_amount
        self.installment_ids = vals
            
            
    @api.constrains('client_id','request_date')
    def check_number_of_client_loan(self):
        for loan in self:
            if loan.client_id and loan.request_date:
                no_of_loan_allow = loan.client_id.loan_request
                start_date = date(date.today().year, 1, 1)
                start_date = start_date.strftime('%Y-%m-%d')
                end_date = date(date.today().year, 12, 31)
                end_date = end_date.strftime('%Y-%m-%d')
                loan_ids = loan.env['dev.loan.loan'].search([('request_date','<=',end_date),('request_date','>=',start_date),('state','not in',['cancel','reject']),('client_id','=',loan.client_id.id)])
                
                if len(loan_ids) > no_of_loan_allow:
                    raise ValidationError(_("This Borrower allow only %s Loan Request in Year !!!")%(no_of_loan_allow))
            
    
    @api.onchange('loan_type_id')
    def onchange_loan_type(self):
        if self.loan_type_id:
            self.interest_rate = self.loan_type_id and self.loan_type_id.rate or 0.0
            self.none_interest_month = self.loan_type_id and self.loan_type_id.none_interest_month or 0
        else:
            self.interest_rate = 0.0
            self.none_interest_month = 0
            
        if self.loan_type_id and self.loan_type_id.proof_ids:
            self.proof_ids = [(6,0, self.loan_type_id.proof_ids.ids)]
        else:
            self.proof_ids = False
            
        if self.loan_type_id:
            self.loan_term = self.loan_type_id.loan_term_by_month
            
            
    
    @api.constrains('loan_term','loan_amount','loan_type_id')        
    def check_rate(self):
        if self.loan_term <= 0:
            raise ValidationError(_("Loan Term Must be Positive !!!"))
                
        if self.loan_amount <= 0:
            raise ValidationError(_("Loan Amount Must be Positive !!!"))
                
        if self.loan_type_id:
            if self.loan_term > self.loan_type_id.loan_term_by_month:
                raise ValidationError(_("Loan Term Must be less then or equal %s Month")%(self.loan_type_id.loan_term_by_month))
        
        if self.loan_type_id and self.loan_amount:
            if self.loan_amount > self.loan_type_id.loan_amount:
                raise ValidationError(_("Loan Amount Must be less then or equal %s Amount")%(self.loan_type_id.loan_amount))
            
        
    @api.model
    def create(self, vals):
        # Assign sequence number only if it passes validation
        loan = super(dev_loan_loan, self).create(vals)
        if loan.name == '/':  # Check if sequence number is not yet assigned
            loan.name = self.env['ir.sequence'].next_by_code('dev.loan.loan') or '/'
        return loan
    
    
    def get_loan_manager_mail(self):
        group_id = self.env.ref('dev_loan_management.group_loan_manager').id
        group_id = self.env['res.groups'].browse(group_id)
        email=''
        if group_id:
            for user in group_id.users:
                if user.partner_id and user.partner_id.email:
                    if email:
                        email = email+','+ user.partner_id.email
                    else:
                        email= user.partner_id.email
        return email
        
        
    def action_confirm_loan(self):
        self.compute_installment()
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data._xmlid_lookup('dev_loan_management.dev_loan_loan_request')[1]
        mtp = self.env['mail.template']
        template_id = mtp.browse(template_id)
        email = self.get_loan_manager_mail()
        template_id.write({'email_to': email})
        template_id.send_mail(self.ids[0], True)
        if self.loan_type_id and self.loan_type_id.is_required_documents:
            if self.percentage != 100.0:
                raise ValidationError(_("not submitted 100% Document so please submit "))
        self.state = 'confirm'
    
    def action_approve_loan(self):
        self.state = 'approve'
        if self.loan_type_id:
            self.loan_account_id = self.loan_type_id.loan_account_id and self.loan_type_id.loan_account_id.id or False
            self.disburse_journal_id = self.loan_type_id.disburse_journal_id and self.loan_type_id.disburse_journal_id.id or False
        self.approve_date = date.today()
        
    def action_set_to_draft(self):
        if self.installment_ids:
            for installment in self.installment_ids:
                installment.unlink()
        self.state = 'draft'
    
    
    
    def get_account_move_vals(self):
        if not self.disburse_journal_id:
            raise ValidationError(_("Select Disburse Journal !!!"))
        vals={
            'date':self.disbursement_date,
            'ref':self.name or 'Loan Disburse',
            'journal_id':self.disburse_journal_id and self.disburse_journal_id.id or False,
            'company_id':self.company_id and self.company_id.id or False,
        }
        return vals
    
    
    def get_credit_lines(self):
        if not self.loan_account_id:
            raise ValidationError(_("Select Disburse Account !!!"))
        vals={
            'partner_id':self.client_id and self.client_id.id or False,
            'account_id':self.loan_account_id and self.loan_account_id.id or False,
            'credit':self.loan_amount,
            'name':self.name or '/',
            'date_maturity':self.disbursement_date,
        }
        return vals
    
    def get_debit_lines(self):
        if self.client_id and not self.client_id.property_account_receivable_id:
            raise ValidationError(_("Select Client Receivable Account !!!"))
        vals={
            'partner_id':self.client_id and self.client_id.id or False,
            'account_id':self.client_id.property_account_receivable_id and self.client_id.property_account_receivable_id.id or False,
            'debit':self.loan_amount,
            'name':self.name or '/',
            'date_maturity':self.disbursement_date,
        }
        return vals
        
        
    
    def action_disburse_loan(self):
        self.disbursement_date = date.today()
        if self.disbursement_date:
            account_move_val = self.get_account_move_vals()
            account_move_id = self.env['account.move'].create(account_move_val)
            vals=[]
            if account_move_id:
                val = self.get_debit_lines()
                vals.append((0,0,val))
                val = self.get_credit_lines()
                vals.append((0,0,val))
                account_move_id.line_ids = vals
                self.disburse_journal_entry_id = account_move_id and account_move_id.id or False
        if self.disburse_journal_entry_id:
            self.state = 'disburse'
        self.compute_installment(self.disbursement_date)
        
    
    
    def action_open_loan(self):
        self.state = 'open'
        
    
    def action_cancel(self):
        self.state = 'cancel'

        


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
