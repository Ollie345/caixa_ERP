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
from odoo.exceptions import ValidationError, AccessError, RedirectWarning,UserError
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


class dev_loan_loan(models.Model):
    _name = "dev.loan.loan"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _description = "Loan"
    
    name = fields.Char('Name', default='/', copy=False)
    client_id = fields.Many2one('res.partner', domain=[('is_allow_loan','=',True)], required="1", string='Borrower')
    request_date = fields.Date('Request Date', default=lambda self: fields.Date.context_today(self), required="1")    
    approve_date = fields.Date('Approve Date', copy=False)
    disbursement_date = fields.Date('Disbursement Date', copy=False)
    loan_type_id = fields.Many2one('dev.loan.type', string='Loan Type', required="1")
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    loan_amount = fields.Monetary('Loan Amount', required="1")
    loan_purpose = fields.Char('Loan Purpose')
    collateral = fields.Char('Collateral')
    source_of_repayment = fields.Char('Source of Repayment')
    is_interest_apply = fields.Boolean(
    string='Apply Interest',
    default=lambda self: self.loan_type_id.is_interest_apply if self.loan_type_id else False)
    interest_rate = fields.Float(string='Interest Rate')
    none_interest_month = fields.Integer(string='None Interest Month')
    loan_term = fields.Integer('Loan Term', required="1")
    interest_mode = fields.Selection(
        [('flat', 'Flat'), 
        ('reducing', 'Reducing')],
        string='Interest Mode',
        default=lambda self: self.loan_type_id.interest_mode if self.loan_type_id else False
        )
    is_amortization_customized = fields.Boolean(
        string='Amortization Customized',
        default=False,
        help='Indicates if amortization settings were customized for this loan')
    is_loan_manager = fields.Boolean(
        string='Is Loan Manager',
        compute='_compute_is_loan_manager',
        help='Technical field to check if current user is a loan manager')
    
    @api.depends()
    def _compute_is_loan_manager(self):
        """Check if current user has loan manager group"""
        for record in self:
            record.is_loan_manager = self.env.user.has_group('dev_loan_management_caixa.group_loan_manager')
    
    state = fields.Selection([('draft','Draft'),
                              ('review','Review'),
                              ('confirm','Confirmed'),
                              ('approve','Approved'),
                              ('disburse','Disbursed'),
                              ('open','Open'),
                              ('close','Closed'),
                              ('cancel','Cancel'),
                              ('reject','Rejected')], string='Status', required="1", default='draft',tracking=1)
    
    
    installment_ids = fields.One2many('dev.loan.installment','loan_id', string='Installments')
    
    total_interest = fields.Monetary('Interest Amount', compute='get_total_interest')
    paid_amount = fields.Monetary('Paid Amount', compute='get_total_interest')
    remaing_amount = fields.Monetary('Remaining Amount', compute='get_total_interest')
    # Outstanding principal used for early closure computation
    balance_amount = fields.Monetary(
        string='Outstanding Principal',
        compute='_compute_balance_amount',
        store=True,
    )
    total_estimated_paid_amount = fields.Monetary('Total Estimated Amount To Pay', compute='get_total_estimated_paid_amount')
    notes = fields.Text('Notes')
    approve_reason = fields.Text('Approve Reason', copy=False)
    approve_user_id = fields.Many2one('res.users','Approved By', copy=False)
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
    
    # Customer Type
    customer_type = fields.Selection(
        selection=[
            ("individual", "Individual"),
            ("company", "Company"),
        ],
        string='Customer Type',
        default="individual",
    )
    
    # Individual Customer Details
    bvn = fields.Char('BVN')
    nin = fields.Char('NIN')
    partner_tin = fields.Char(string="TIN")
    bank_name = fields.Char('Bank Name')
    account_number = fields.Char('Account Number')
    marital_status = fields.Char('Marital Status')
    applicant_title = fields.Char('Applicant Title')
    applicant_address = fields.Char('Applicant Address')
    
    # Next of Kin Details
    nok_name = fields.Char('Next Of Kin Name')
    nok_phone = fields.Char('Next Of Kin Phone')
    nok_address = fields.Char('Next Of Kin Address')
    nok_relationship = fields.Char('Next Of Kin Relationship')
    nok_occupation = fields.Char('Next Of Kin Occupation')
    nok_email = fields.Char('Next Of Kin Email')
    
    # Employment Details
    employment_company_name = fields.Char('Company Name')
    employment_company_address = fields.Char('Company Address')
    employment_company_email = fields.Char('Company Email')
    salary = fields.Float('Salary')
    service_length = fields.Integer('Length of Service')
    designation = fields.Char('Designation')
    
    # Guarantor Details
    guarantor_title = fields.Char('Guarantor Title')
    guarantor_name = fields.Char('Guarantor Name')
    guarantor_phone = fields.Char('Guarantor Phone')
    guarantor_email = fields.Char('Guarantor Email')
    guarantor_relationship = fields.Char('Guarantor Relationship')
    
    # Corporate Customer Details
    company_phone = fields.Char('Phone Number')
    date_of_incorporation = fields.Date('Date of Incorporation')
    annual_turnover = fields.Float('Annual Turnover')
    company_rc_number = fields.Char('RC Number')
    company_bank_name = fields.Char('Bank Name')
    company_bank_account_number = fields.Char('Bank Account Number')
    company_bank_account_name = fields.Char('Bank Account Name')
    
    # Director Information
    director_title = fields.Char("Director's Title")
    director_name = fields.Char('Director\'s Name')
    director_phone = fields.Char('Director\'s Phone')
    director_email = fields.Char('Director\'s Email')
    director_nin = fields.Char('Director\'s NIN')
    director_date_of_birth = fields.Date('Director\'s Date of Birth')
    director_bvn = fields.Char('Director\'s BVN')
    director_address = fields.Char('Director\'s Address')
    director_marital_status = fields.Char('Director\'s Marital Status')
    director_designation = fields.Char('Director\'s Designation')
    
    # Document URLs (clickable links shown in the form)
    loan_document_url = fields.Char('Loan Document URL')
    passport_url = fields.Char('Passport URL')
    govt_issued_id_url = fields.Char('Govt. ID URL')
    staff_id_url = fields.Char('Staff ID URL')
    pay_slip_url = fields.Char('Pay Slip URL')
    bank_statement_url = fields.Char('Bank Statement URL')
    utility_bill_url = fields.Char('Utility Bill URL')
    certificate_of_incorporation_url = fields.Char('Certificate of Incorporation URL')
    
    # Document URL lists (raw JSON strings to preserve all links)
    loan_document_urls = fields.Text('Loan Document URLs')
    passport_urls = fields.Text('Passport URLs')
    govt_issued_id_urls = fields.Text('Govt. ID URLs')
    staff_id_urls = fields.Text('Staff ID URLs')
    pay_slip_urls = fields.Text('Pay Slip URLs')
    bank_statement_urls = fields.Text('Bank Statement URLs')
    utility_bill_urls = fields.Text('Utility Bill URLs')
    certificate_of_incorporation_urls = fields.Text('Certificate of Incorporation URLs')
    
    # External metadata
    external_reference = fields.Char('External Reference')
    external_status = fields.Char('External Status')
    external_kyc_id = fields.Char('External KYC ID')

    # checklist
    comment = fields.Char('Comment')
    checklist_item_ids = fields.Many2many(
        "dev.checklist.template.line",
        string="Checklist"
    )

    # fields for the penalty
    grace_period = fields.Integer(
        string="Grace Period (Days)",
        related="loan_type_id.grace_period",
        store=True
    )

    penalty_rate = fields.Float(
        string="Daily Penalty Rate (%)",
        related="loan_type_id.penalty_rate",
        store=True
    )

    closure_date = fields.Date(
        string="Closure Date",
        tracking=True
    )

    closure_amount = fields.Monetary(
        string="Closure Amount",
        # compute="_compute_closure_amount",
        store=True,
        tracking=True
    )

    is_early_closure = fields.Boolean(
        string="Early Closure",
        default=False
    )

    # Calculate the internal penalty
    def _calculate_penalty(self):
        today = date.today()
        penalty_total = 0.0

        # Loop through loan installments
        for inst in self.installment_ids:

            # Skip paid installments
            if inst.state == 'paid':
                continue

            # Skip installments with no due date
            if not inst.due_date:
                continue

            # Grace period logic
            penalty_start = inst.due_date + timedelta(days=self.grace_days)

            if today <= penalty_start:
                continue  # Still in grace period → no penalty

            # Number of overdue days
            overdue_days = (today - penalty_start).days

            # Calculate penalty: Opening Balance × Penalty Rate × Days elapsed after grace period
            # Penalty per day = Opening Balance × Penalty Rate
            # Total Penalty = Penalty per day × Overdue Days
            if self.penalty_rate:
                penalty_total += inst.balance * (self.penalty_rate / 100) * overdue_days

        return penalty_total

    # Cron Jo applies Penalty
    def cron_apply_daily_penalties(self):
        today = date.today()

        loans = self.search([
            ('state', 'in', ['approved', 'disbursed']),
        ])

        for loan in loans:

            # Prevent double-run in one day
            if loan.last_penalty_calc_date == today:
                continue

            # Calculate penalty
            new_penalty = loan._calculate_penalty()

            loan.write({
                'penalty_amount': new_penalty,
                'last_penalty_calc_date': today
            })

    #button action to compute closure
    def action_compute_closure(self):
        for loan in self:
            if loan.state != 'open':
                raise UserError(_("Loan must be open to compute closure."))

            # if not loan.closure_date:
            #     raise UserError(_("Please select a closure date."))

            # loan.is_early_closure = True
            # loan._compute_closure_amount()

            return {
                'name': _('Early Loan Closure'),
                'type': 'ir.actions.act_window',
                'res_model': 'dev.loan.closure.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_loan_id': self.id,
                    'default_closure_date': fields.Date.context_today(self),
                }
            }

        # New button action to open the wizard
        # def action_compute_closure(self):
        #     self.ensure_one()
        #
        #     if self.state != 'open':
        #         raise UserError(_("Loan must be open to compute closure."))
        #
        #     # Create an instance of the wizard
        #     wizard_vals = {
        #         'loan_id': self.id,
        #         'closure_date': fields.Date.today(),
        #     }
        #
        #     wizard = self.env['dev.loan.closure.wizard'].create(wizard_vals)
        #
        #     # Open the wizard form view
        #     return {
        #         'name': _('Early Loan Closure'),
        #         'type': 'ir.actions.act_window',
        #         'res_model': 'dev.loan.closure.wizard',
        #         'view_mode': 'form',
        #         'res_id': wizard.id,
        #         'target': 'new',
        #         'context': self.env.context,
        #     }

    # send closure email
    def _send_closure_email(self):
        template = self.env.ref(
            'dev_loan_management_caixa.mail_template_early_loan_closure',
            raise_if_not_found=False
        )
        if template:
            template.send_mail(self.id, force_send=True)

    @api.onchange('loan_type_id')
    def _onchange_loan_type(self):
        for rec in self:
            rec.checklist_item_ids = [(5, 0, 0)]  # Clear
            if rec.loan_type_id and rec.loan_type_id.loan_officer_id:
                rec.user_id = rec.loan_type_id.loan_officer_id.id

    @api.model
    def create(self, vals):
        if vals.get('loan_type_id'):
            loan_type = self.env['dev.loan.type'].browse(vals.get('loan_type_id'))
            if loan_type and loan_type.loan_officer_id:
                vals['user_id'] = loan_type.loan_officer_id.id
        return super(dev_loan_loan, self).create(vals)

    def compute_loan_notice_count(self):
       for loan in self:
            loan_ids=self.env['ln.notice'].search([('partner_id','=',self.client_id.id),('loan_id','=',self.id)])
            loan.loan_notice = len(loan_ids)  

    def view_loan_notice(self):
         loan_ids=self.env['ln.notice'].search([('partner_id','=',self.client_id.id),('loan_id','=',self.id)])
         list_id = loan_ids.ids
         action = self.env.ref('dev_loan_management_caixa.action_dev_loan_notice').sudo().read()[0]
         if len(list_id) > 1:
            action['domain'] = [('id', 'in', list_id)]
         elif len(list_id) == 1:
            action['views'] = [(self.env.ref('dev_loan_management_caixa.view_dev_loan_notice_form').id, 'form')]
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
         action = self.env.ref('dev_loan_management_caixa.action_dev_loan_agreement').sudo().read()[0]
         if len(list_id) > 1:
            action['domain'] = [('id', 'in', list_id)]
         elif len(list_id) == 1:
            action['views'] = [(self.env.ref('dev_loan_management_caixa.view_dev_loan_agreement_form').id, 'form')]
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
            loan_type_action = self.env.ref('dev_loan_management_caixa.action_dev_loan_type')
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
            loan_type_action = self.env.ref('dev_loan_management_caixa.action_dev_loan_type')
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
            action = self.env.ref('dev_loan_management_caixa.action_dev_loan_installment').read()[0]
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
                # Equal Principal Amortization Formula
                # Principal per month = Loan Amount / Number of Months
                principal_per_month = loan.loan_amount / loan.loan_term
                
                # For EMI estimate, use first month payment (highest interest)
                # Interest on full loan amount for first month (rate is already monthly)
                first_month_interest = (loan.loan_amount * (loan.interest_rate / 100))
                
                # EMI estimate = Principal + First Month Interest
                loan.emi_estimate = principal_per_month + first_month_interest
            else:
                # No interest case
                if loan.loan_amount and loan.loan_term:
                    loan.emi_estimate = loan.loan_amount / loan.loan_term
                    
                    
    def _make_url(self):
        ir_param = self.env['ir.config_parameter'].sudo()
        base_url = ir_param.get_param('web.base.url')
        menu_id = self.env.ref('dev_loan_management_caixa.menu_dev_loan_request_approve').id
        action_id = self.env.ref('dev_loan_management_caixa.action_dev_loan_loan_approve').id
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
    
    @api.depends('installment_ids', 'installment_ids.state', 'installment_ids.amount')
    def _compute_balance_amount(self):
        """Compute outstanding principal from unpaid installments."""
        for loan in self:
            balance = 0.0
            for inst in loan.installment_ids:
                if inst.state != 'paid':
                    balance += inst.amount or 0.0
            loan.balance_amount = balance
            
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
        if self.state == 'review':
            date = self.request_date
        else:
            date = date
        vals = []
        interest_account_id,installment_account_id,loan_payment_journal_id = self.get_loan_account_journal()
        
        # Equal Principal Formula: Principal Amount = Loan Amount / Number of Months
        principal_per_month = self.loan_amount / self.loan_term
        
        for i in range(1,self.loan_term+1):
            # Principal payment is constant (equal principal amortization)
            principal = principal_per_month
            
            # Adjust for final payment if remaining balance is less than principal
            if opening_balance < principal:
                principal = opening_balance
            
            # Monthly Interest = Monthly Interest Rate × Remainder of Loan Amount
            if self.interest_rate:
                if self.interest_mode == 'flat':
                    # Flat interest: calculated on original loan amount (rate is already monthly)
                    interest = (self.loan_amount * (self.interest_rate / 100))
                else:
                    # Reducing balance: calculated on remaining balance (rate is already monthly)
                    interest = (opening_balance * (self.interest_rate / 100))
            else:
                interest = 0.0
            
            interest = float("{:.2f}".format(interest))
            principal = float("{:.2f}".format(principal))
            
            # Calculate closing balance
            closing_amount = opening_balance - principal
            
            # Handle none interest months
            none_interest = False
            if i <= self.none_interest_month:
                none_interest = True
                interest = 0.0
                # For none interest months, only principal is paid
                closing_amount = opening_balance - principal
            
            # Ensure closing balance doesn't go negative
            if closing_amount < 0.0:
                closing_amount = 0.0
                # Adjust principal if needed
                principal = opening_balance
            
            # Calculate total payment
            total_payment = principal + interest
            
            # Increment date by 30 days (each month = 30 days)
            date = date + relativedelta(days=30)
            
            vals.append((0, 0,{
                'name':'INS - '+self.name+ ' - '+str(i),
                'client_id':self.client_id and self.client_id.id or False,
                'date':date,
                'opening_balance':opening_balance,
                'amount':principal,
                'none_interest':none_interest,
                'interest':interest,
                'closing_balance':closing_amount,
                'total_amount':float("{:.2f}".format(total_payment)),
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
                # Exclude the current loan from the count
                loan_ids = loan.env['dev.loan.loan'].search([
                    ('request_date', '<=', end_date),
                    ('request_date', '>=', start_date),
                    ('state', 'not in', ['cancel', 'reject']),
                    ('client_id', '=', loan.client_id.id),
                    ('id', '!=', loan.id)  # Exclude current loan
                ])
                
                if len(loan_ids) > no_of_loan_allow:
                    raise ValidationError(_("This Borrower allow only %s Loan Request in Year !!!") % no_of_loan_allow)
            
    
    @api.onchange('loan_type_id')
    def onchange_loan_type(self):
        if self.loan_type_id:
            # Only set defaults if not already customized
            if not self.is_amortization_customized:
                self.interest_rate = self.loan_type_id.rate or 0.0
                self.none_interest_month = self.loan_type_id.none_interest_month or 0
                # Always set interest_mode from loan type when loan_type changes
                if self.loan_type_id.interest_mode:
                    self.interest_mode = self.loan_type_id.interest_mode
                else:
                    self.interest_mode = False
                self.is_interest_apply = self.loan_type_id.is_interest_apply or False
            # Always set loan term from type (unless customized)
            if not self.is_amortization_customized:
                self.loan_term = self.loan_type_id.loan_term_by_month
        else:
            if not self.is_amortization_customized:
                self.interest_rate = 0.0
                self.none_interest_month = 0
                self.interest_mode = False
                self.is_interest_apply = False
            
        if self.loan_type_id and self.loan_type_id.proof_ids:
            self.proof_ids = [(6, 0, self.loan_type_id.proof_ids.ids)]
        else:
            self.proof_ids = False
    
    def action_customize_amortization(self):
        """Mark amortization settings as customized - allows CAT team to override loan type defaults"""
        self.ensure_one()
        if not self.env.user.has_group('dev_loan_management_caixa.group_loan_manager'):
            raise AccessError(_("Only Loan Managers can customize amortization settings."))
        self.is_amortization_customized = True
        return True
    
    @api.onchange('interest_rate', 'interest_mode', 'none_interest_month', 'loan_term', 'is_interest_apply')
    def onchange_amortization_fields(self):
        """Auto-mark as customized if any amortization field is manually changed"""
        if self.loan_type_id and not self.is_amortization_customized:
            # Check if current values differ from loan type defaults
            if (self.interest_rate != self.loan_type_id.rate or
                self.interest_mode != self.loan_type_id.interest_mode or
                self.none_interest_month != self.loan_type_id.none_interest_month or
                self.loan_term != self.loan_type_id.loan_term_by_month or
                self.is_interest_apply != self.loan_type_id.is_interest_apply):
                self.is_amortization_customized = True
            
    
    @api.constrains('customer_type', 'bvn', 'nin')
    def _check_individual_required_fields(self):
        """Validate that BVN and NIN are required for Individual customers"""
        for record in self:
            if record.customer_type == 'individual':
                if not record.bvn or (isinstance(record.bvn, str) and not record.bvn.strip()):
                    raise ValidationError(_("BVN is required for Individual customers."))
                if not record.nin or (isinstance(record.nin, str) and not record.nin.strip()):
                    raise ValidationError(_("NIN is required for Individual customers."))
    
    @api.constrains('loan_term','loan_amount','loan_type_id')        
    def check_rate(self):
        if self.loan_term <= 0:
            raise ValidationError(_("Loan Term Must be Positive !!!"))
                
        if self.loan_amount <= 0:
            raise ValidationError(_("Loan Amount Must be Positive !!!"))
        
        # Only enforce loan type limits if not customized
        if self.loan_type_id and not self.is_amortization_customized:
            if self.loan_term > self.loan_type_id.loan_term_by_month:
                raise ValidationError(_("Loan Term Must be less than or equal %s Month") % (self.loan_type_id.loan_term_by_month))
        
        if self.loan_type_id and self.loan_amount:
            if not self.is_amortization_customized and self.loan_amount > self.loan_type_id.loan_amount:
                raise ValidationError(_("Loan Amount Must be less than or equal %s Amount") % (self.loan_type_id.loan_amount))
            
        
    @api.model
    def create(self, vals):
        # Normalize external customer_type values to the internal selection keys
        # consumer -> individual, corporate -> company
        ct = vals.get('customer_type')
        if ct is not None:
            ct_lower = str(ct).lower()
            if ct_lower == 'consumer':
                vals['customer_type'] = 'individual'
            elif ct_lower == 'corporate':
                vals['customer_type'] = 'company'
        
        # Populate customer details from lead if lead_id is provided
        lead_id = vals.get('lead_id')
        if lead_id:
            lead = self.env['crm.lead'].browse(lead_id)
            if lead.exists():
                # Map customer details from lead to loan
                customer_fields = [
                    'customer_type', 'bvn', 'nin', 'partner_tin', 'bank_name', 'account_number',
                    'marital_status', 'applicant_title', 'applicant_address',
                    'nok_name', 'nok_phone', 'nok_address', 'nok_relationship', 'nok_occupation', 'nok_email',
                    'salary', 'service_length', 'designation',
                    'guarantor_title', 'guarantor_name', 'guarantor_phone', 'guarantor_email', 'guarantor_relationship',
                    'company_phone', 'date_of_incorporation', 'annual_turnover', 'company_rc_number',
                    'company_bank_name', 'company_bank_account_number', 'company_bank_account_name',
                    'director_title', 'director_name', 'director_phone', 'director_email', 'director_nin',
                    'director_date_of_birth', 'director_bvn', 'director_address', 'director_marital_status', 'director_designation',
                    'loan_document_url', 'passport_url', 'govt_issued_id_url', 'staff_id_url', 'pay_slip_url',
                    'bank_statement_url', 'utility_bill_url', 'certificate_of_incorporation_url',
                    'loan_document_urls', 'passport_urls', 'govt_issued_id_urls', 'staff_id_urls',
                    'pay_slip_urls', 'bank_statement_urls', 'utility_bill_urls', 'certificate_of_incorporation_urls',
                    'external_reference', 'external_status', 'external_kyc_id'
                ]
                # Map employment company fields (lead uses company_name, loan uses employment_company_name)
                if lead.customer_type == 'individual':
                    if lead.company_name and not vals.get('employment_company_name'):
                        vals['employment_company_name'] = lead.company_name
                    if lead.company_address and not vals.get('employment_company_address'):
                        vals['employment_company_address'] = lead.company_address
                    if lead.company_email and not vals.get('employment_company_email'):
                        vals['employment_company_email'] = lead.company_email
                
                for field in customer_fields:
                    if hasattr(lead, field) and field not in vals and getattr(lead, field, False):
                        vals[field] = getattr(lead, field)
        
        # Assign sequence number only if it passes validation
        loan = super(dev_loan_loan, self).create(vals)
        if loan.name == '/':  # Check if sequence number is not yet assigned
            loan.name = self.env['ir.sequence'].next_by_code('dev.loan.loan') or '/'
        return loan
    
    
    def get_loan_manager_mail(self):
        group_id = self.env.ref('dev_loan_management_caixa.group_loan_manager').id
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

    # SUbmit for review button
    def action_submit_loan(self):
        self.ensure_one()
        self.write({'state': 'review'})

    def action_confirm_loan(self):
        self.compute_installment()
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data._xmlid_lookup('dev_loan_management_caixa.dev_loan_loan_request')[1]
        mtp = self.env['mail.template']
        template_id = mtp.browse(template_id)
        email = self.get_loan_manager_mail()
        template_id.write({'email_to': email})
        template_id.send_mail(self.ids[0], True)
        if self.loan_type_id and self.loan_type_id.is_required_documents:
            if self.percentage != 100.0:
                raise ValidationError(_("not submitted 100% Document so please submit "))
        self.state = 'confirm'

    def action_approve_loan(self, reason=None):
        """Approve the loan directly or via wizard.
        If `reason` is provided, it sets approve_reason; otherwise it stays empty."""
        for loan in self:
            loan.state = 'approve'
            loan.approve_user_id = self.env.user
            loan.approve_date = date.today()
            if reason:
                loan.approve_reason = reason

            # Set account and journal if loan type is defined
            if loan.loan_type_id:
                loan.loan_account_id = loan.loan_type_id.loan_account_id.id if loan.loan_type_id.loan_account_id else False
                loan.disburse_journal_id = loan.loan_type_id.disburse_journal_id.id if loan.loan_type_id.disburse_journal_id else False

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
        # Only set to today if not already set (allows manual date selection for testing)
        if not self.disbursement_date:
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
