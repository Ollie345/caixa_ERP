# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################
from odoo import fields, models

class ln_document(models.Model):
    _name = 'ln.base.documents'
    _description = 'Loan Document'
    _order = "name"
    
    def move_to_complete(self):
        self.state = 'done'
        
    def move_to_cancel(self):
        self.state = 'cancel'
    

    name = fields.Char('Name',required='1')
    document_type_id=fields.Many2one('ln.document.type',string="Document Type")
    description =fields.Html('Description')
    state = fields.Selection(string='Status',selection=[('draft','Draft'),('done','Done'),('cancel','Cancelled')],default='draft',readonly=True)
    loan_id=fields.Many2one('dev.loan.loan' ,string='Loan Detail')
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
