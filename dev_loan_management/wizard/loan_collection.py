# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##########################################################################

from odoo import fields, models,api

class loancollection(models.TransientModel):

    _name = 'loan.collection.wizard'
    _description="Loan Collection"

    current_month=fields.Boolean(string="Current Month Collection" , default=True)
    next_month=fields.Boolean(string="Next month's Collection")
    overdue_month=fields.Boolean(string="Overdue Month Collection")

    def action_print_pdf(self):
        
        return self.env.ref('dev_loan_management.action_report_loan_collection').report_action(self, data=None)

    

