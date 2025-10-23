# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import api, fields, models, _


class dev_create_loan_task(models.TransientModel):
    _name = "create.loan.task"
    _description = "Creat Loan Task Wizard"
    
    def default_get(self, fields):
        defaults = super(dev_create_loan_task, self).default_get(fields)
        active_ids = self._context.get('active_ids')
        loan = self.env['dev.loan.loan'].browse(active_ids)
        if loan and loan.client_id:
            defaults['partner_id'] = loan.client_id.id
        return defaults
   
    name = fields.Char(string="Name")
    user_id = fields.Many2one('res.users',string="Assigned to",default=lambda self: self.env.user)
    project_id = fields.Many2one('project.project',string="Project")
    date_deadline = fields.Date(string="Deadline",default=fields.Date.today())
    partner_id = fields.Many2one('res.partner',string="Borrower")
    tag_ids = fields.Many2many('project.tags',string="Tag")
    loan_id = fields.Many2one('dev.loan.loan',string="Loan" )

    def create_task(self):
        active_ids = self._context.get('active_ids')
        loan_id = self.env['dev.loan.loan'].browse(active_ids)
        vals={
            'name':self.name,
            'user_ids':self.user_id and self.user_id.ids or False,
            'date_deadline':self.date_deadline,
            'partner_id':self.partner_id and self.partner_id.id or False,
            'project_id':self.project_id and self.project_id.id or False,
            'tag_ids':self.tag_ids and self.tag_ids.ids or False,
            'loan_id':loan_id and loan_id.id,
             }
        task_id = self.env['project.task'].create(vals)
        return True
       
       
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:




