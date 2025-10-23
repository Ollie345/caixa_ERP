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

class Agreement_loan(models.AbstractModel): 
    _name = 'report.dev_loan_management.loan_agreement_template'
    _description = "Loan Agreement Report"

#    @api.multi
#    def get_footer_text(self,roote_number, cheque_num):
#        if roote_number and cheque_num:
#            return str(roote_number)+' '+ str(cheque_num)   
    # def get_agreement_detail(self):
    #     pass   
            
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['ln.agreement'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'ln.agreement',
            'docs': docs,
            # 'get_agreement_detail': self.get_agreement_detail()

#            'get_footer_text':self.get_footer_text,
        }
