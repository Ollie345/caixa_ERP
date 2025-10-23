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
    borrower_category_id = fields.Many2one('borrower.category',string="Borrower Category")
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
    
    
    loan_ids = fields.One2many('dev.loan.loan','client_id', string='Loans', domain=[('state','not in', ['draft','reject','cancel'])])
    count_loan = fields.Integer('View Loan', compute='_count_loan', store=True)
    
    @api.depends('loan_ids')
    def _count_loan(self):
        for partner in self:
            partner.count_loan = len(partner.loan_ids)
            
    def action_view_loan(self):
        loan_ids = self.env['dev.loan.loan'].search([('client_id','=',self.id)])
        if loan_ids:
            action = self.env.ref('dev_loan_management.action_dev_loan_loan').read()[0]
            action['domain'] = [('id', 'in', loan_ids.ids),('state','not in',['draft','reject','cancel'])]
            return action
        else:
            action = {'type': 'ir.actions.act_window_close'}
    
    def action_view_installment(self):
        installment_ids = self.env['dev.loan.installment'].search([('client_id','=',self.id)])
        if installment_ids:
            action = self.env.ref('dev_loan_management.action_dev_loan_installment').read()[0]
            action['domain'] = [('id', 'in', installment_ids.ids),('loan_id.state','not in',['draft','reject','cancel'])]
            return action
        else:
            action = {'type': 'ir.actions.act_window_close'}
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

