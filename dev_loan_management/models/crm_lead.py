# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import fields, models, api

class loan_lead(models.Model):
    _inherit = 'crm.lead'
    
    
    def create_loan_request(self):
        vals = {
            'client_id': self.partner_id.id if self.partner_id else False,
            'loan_type_id': self.loan_type_id.id if self.loan_type_id else False,
            'loan_amount': self.loan_amount,
            'loan_term' : self.loan_term, 
            'lead_id': self.id,
        }
        loan_request = self.env['dev.loan.loan'].create(vals)
        loan_request.onchange_loan_type()
        if loan_request and loan_request.client_id:
            loan_request.client_id.is_allow_loan = True
        return True
        
        
    def _compute_loan_count(self):
        for lead in self:
            loan_ids = self.env['dev.loan.loan'].search([('lead_id','=',self.id)])
            lead.loan_count = len(loan_ids)
            
    def action_view_loan(self):
        action = self.env.ref('dev_loan_management.action_dev_loan_loan').read()[0]
        loan_ids = self.env['dev.loan.loan'].search([('lead_id','=',self.id)])
        if len(loan_ids) > 1:
            action['domain'] = [('id', 'in', loan_ids.ids)]
        elif loan_ids:
            action['views'] = [(self.env.ref('dev_loan_management.view_dev_loan_loan_form').id, 'form')]
            action['res_id'] = loan_ids.id
        return action
            

    #Loan Details
    loan_type_id = fields.Many2one('dev.loan.type', string='Loan Type')
    loan_amount = fields.Float('Requested Amount')
    loan_term = fields.Integer('Loan Term')
    loan_id = fields.Many2one('dev.loan.loan',string="Loan")
    loan_count = fields.Integer(string='Loan Request', compute='_compute_loan_count')
    collateral = fields.Char('Collateral')
    source_of_repayment = fields.Char('Source of Repayment')
    loan_purpose = fields.Char('Loan Purpose')

    #Other Application Details
    bvn = fields.Char('BVN')
    nin = fields.Char('NIN')
    bank_name = fields.Char('Bank Name')
    account_number = fields.Char('Account Number')
    marital_status = fields.Selection([('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced'), ('widowed', 'Widowed')], string='Marital Status')

    #Next of Kin Details
    nok_name = fields.Char('Next Of Kin Name')
    nok_phone = fields.Char('Next Of Kin Phone')
    nok_address = fields.Char('Next Of Kin Address')
    nok_relationship = fields.Char('Next Of Kin Relationship')
    nok_occupation = fields.Char('Next Of Kin Occupation')
    nok_email = fields.Char('Next Of Kin Email')

    #Employment Details
    company_name = fields.Char('Company Name')
    company_address = fields.Char('Company Address')
    company_email = fields.Char('Company Email')
    salary = fields.Float('Salary')
    service_length = fields.Integer('Length of Service')
    designation = fields.Char('Designation')

    #Guarantor Details
    guarantor_name = fields.Char('Guarantor Name')
    guarantor_phone = fields.Char('Guarantor Phone')
    guarantor_email = fields.Char('Guarantor Email')
    guarantor_relationship = fields.Char('Guarantor Relationship')

    # Form Controls
    customer_type = fields.Selection(
        selection=[
            ("individual", "Individual"),
            ("company", "Company"),
        ],
        string='Customer Type',
        required=False,
        default="individual",
    )

    attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        string='Attachments',
        domain=[('res_model', '=', 'crm.lead')],
    )

    #CORPORATE LOAN DETAILS

    #Company Information
    company_name = fields.Char('Company Name')
    company_email = fields.Char('Company Email')
    company_phone = fields.Char('Phone Number')
    date_of_incorporation = fields.Date('Date of Incorporation')
    annual_turnover = fields.Float('Annual Turnover')
    company_rc_number = fields.Char('RC Number')
    company_bank_name = fields.Char('Bank Name')
    company_bank_account_number = fields.Char('Bank Account Number')
    company_bank_account_name = fields.Char('Bank Account Name')

    #Director Information
    director_name = fields.Char('Director\'s Name')
    director_phone = fields.Char('Director\'s Phone')
    director_email = fields.Char('Director\'s Email')
    director_nin = fields.Char('Director\'s NIN')
    director_date_of_birth = fields.Date('Director\'s Date of Birth')
    director_bvn = fields.Char('Director\'s BVN')
    director_address = fields.Char('Director\'s Address')
    director_marital_status = fields.Selection([
        ('single', 'Single'), 
        ('married', 'Married'), 
        ('divorced', 'Divorced'), 
        ('widowed', 'Widowed')], 
        string='Director\'s Marital Status')
    director_designation = fields.Char('Director\'s Designation')
    

