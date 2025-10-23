# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import models, fields

class ln_co_borrower(models.Model):
    _name = "ln.co.borrower"
    _description = "Loan Co Borrower"
    
    loan_id=fields.Many2one('dev.loan.loan',string='Loan')
    name=fields.Char(string='Name')
    relation_id = fields.Many2one('ln.co.borrower.relation', string='Relation')
    contact_no=fields.Char(string='Contact')
    address=fields.Text(string='Address')
 
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: 
