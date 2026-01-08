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


class res_partner(models.Model):
    _inherit = "res.partner"
    
    is_allow_loan = fields.Boolean('Allow Loan')
    loan_request = fields.Integer('Loan Request Per Year', default=1)
    # Add after line 24 (after available_peppol_eas field)
    bvn = fields.Char('BVN', copy=False, help='Bank Verification Number')
    nin = fields.Char('NIN', copy=False, help='National Identification Number')
    borrower_category_id = fields.Many2one('borrower.category',string="Borrower Category")
    # Fallback field to satisfy views referencing this field from other modules
    duplicate_bank_partner_ids = fields.Boolean(string="Duplicate Bank Partners", default=False)
    # Fallback placeholder for base view compatibility in some editions
    available_peppol_eas = fields.Char(string="Available PEPPOL EAS")
    is_active_borrower = fields.Boolean(
        compute='_compute_borrower_status', store=True,
        string="Is Active Borrower"
    )
    is_past_borrower = fields.Boolean(
        compute='_compute_borrower_status', store=True,
        string="Is Past Borrower"
    )
    
    @api.depends('loan_ids.state')
    def _compute_borrower_status(self):
        for partner in self:
            active_states = {'open', 'approve', 'disburse', 'confirm'}
            past_states = {'reject', 'close', 'cancel'}
            # Evaluate against ALL loans for this partner (ignoring domain on loan_ids)
            all_loans = self.env['dev.loan.loan'].sudo().search([('client_id', '=', partner.id)])
            has_active = any(loan.state in active_states for loan in all_loans)
            has_past = any(loan.state in past_states for loan in all_loans)
            partner.is_active_borrower = has_active
            partner.is_past_borrower = (not has_active) and has_past
    
    @api.constrains('is_allow_loan','loan_request')        
    def check_rate(self):
        if self.is_allow_loan and self.loan_request <= 0:
            raise ValidationError(_("Loan Request Per Year Must be Positive !!!"))

# Add this method after line 52 in res_partner.py (after the check_rate method):

    @api.onchange('borrower_category_id')
    def _onchange_borrower_category_id(self):
        """Automatically set loan_request from borrower category"""
        if self.borrower_category_id and self.borrower_category_id.loan_request_per_year:
            self.loan_request = self.borrower_category_id.loan_request_per_year
    
    def write(self, vals):
        """Override write to set loan_request when borrower_category_id is updated"""
        if 'borrower_category_id' in vals and vals['borrower_category_id']:
            category = self.env['borrower.category'].browse(vals['borrower_category_id'])
            if category and category.loan_request_per_year:
                vals['loan_request'] = category.loan_request_per_year
        return super().write(vals)
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set loan_request when borrower_category_id is set"""
        for vals in vals_list:
            if 'borrower_category_id' in vals and vals['borrower_category_id']:
                category = self.env['borrower.category'].browse(vals['borrower_category_id'])
                if category and category.loan_request_per_year:
                    vals['loan_request'] = category.loan_request_per_year
        return super().create(vals_list)
    
    
    loan_ids = fields.One2many('dev.loan.loan','client_id', string='Loans', domain=[('state','not in', ['draft','reject','cancel'])])
    count_loan = fields.Integer('View Loan', compute='_count_loan', store=True)
    
    @api.depends('loan_ids')
    def _count_loan(self):
        for partner in self:
            partner.count_loan = len(partner.loan_ids)
            
    def action_view_loan(self):
        loan_ids = self.env['dev.loan.loan'].search([('client_id','=',self.id)])
        if loan_ids:
            action = self.env.ref('dev_loan_management_caixa.action_dev_loan_loan').read()[0]
            action['domain'] = [('id', 'in', loan_ids.ids),('state','not in',['draft','reject','cancel'])]
            return action
        else:
            action = {'type': 'ir.actions.act_window_close'}
    
    def action_view_installment(self):
        installment_ids = self.env['dev.loan.installment'].search([('client_id','=',self.id)])
        if installment_ids:
            action = self.env.ref('dev_loan_management_caixa.action_dev_loan_installment').read()[0]
            action['domain'] = [('id', 'in', installment_ids.ids),('loan_id.state','not in',['draft','reject','cancel'])]
            return action
        else:
            action = {'type': 'ir.actions.act_window_close'}
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

