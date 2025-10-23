# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import models, fields, api

class Notice_loan(models.AbstractModel): 
    _name = 'report.dev_loan_management.loan_notice_template'
    _description = "Loan Notice Report"

            
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['ln.notice'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'ln.notice',
            'docs': docs,
           
        }
