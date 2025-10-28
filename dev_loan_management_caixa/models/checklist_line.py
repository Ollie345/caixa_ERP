# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import models, fields,api
from datetime import date,datetime

class loan_checklist_line(models.Model):
    _name ='checklist.line'
    _description = 'checklist line'
    
    
    @api.onchange('checklist_id')
    def onchange_checklist_id(self):
        if self.checklist_id:
            self.description = self.checklist_id and self.checklist_id.description or ''
            self.state = self.checklist_id and self.checklist_id.state   or ''
            self.document_type_id = self.checklist_id and self.checklist_id.document_type_id and self.checklist_id.document_type_id.id  or ''
            
            
    def move_to_complete(self):
        self.state = 'done'
        
        
    def move_to_cancel(self):
        self.state = 'cancel'
    
    @api.onchange('state')
    def onchange_state(self):
        if self.state:
            self.state = 'draft'
    
    
    document_id = fields.Many2one('ln.base.documents',string='Name')
    state = fields.Selection(string='Status',selection=[('draft','Draft'),('done','Done'),('cancel','Cancelled')],default='draft',readonly=True)
    loan_id = fields.Many2one('dev.loan.loan',string='Loan Order')
    document_type_id=fields.Many2one('ln.document.type',string="Document Type")
    description =fields.Html('Description')
    
  

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
