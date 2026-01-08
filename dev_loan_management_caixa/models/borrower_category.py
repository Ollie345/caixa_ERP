# Replace the entire file content with:
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


class borrower_category(models.Model):
    _name = "borrower.category"
    _description = "Borrower Category"
    
    name = fields.Char('Name', required="1", copy=False)
    loan_request_per_year = fields.Integer(
        string='Loan Request Per Year',
        required=True,
        default=1,
        help='Number of loan requests allowed per year for borrowers in this category'
    )
    is_default = fields.Boolean(
        string='Is Default',
        default=False,
        help='Mark this category as the default category for new borrowers'
    )
    
    @api.constrains('loan_request_per_year')
    def _check_loan_request_per_year(self):
        for record in self:
            if record.loan_request_per_year <= 0:
                raise ValidationError(_("Loan Request Per Year must be positive."))
    
    @api.constrains('is_default')
    def _check_default_category(self):
        for record in self:
            if record.is_default:
                # Ensure only one default category exists
                other_defaults = self.search([
                    ('id', '!=', record.id),
                    ('is_default', '=', True)
                ])
                if other_defaults:
                    raise ValidationError(_("Only one borrower category can be set as default."))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: