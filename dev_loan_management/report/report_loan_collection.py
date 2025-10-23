# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import models,fields
from datetime import datetime, timedelta 
from dateutil.relativedelta import relativedelta




class LoanCollectionReport(models.AbstractModel):
    _name = 'report.dev_loan_management.loan_collection_template'

    
   

    # def get_current_installments(self, wizard_id):
    
    #     today = datetime.today()
    #     current_month = today.month
    #     current_year = today.year

        
    #     filtered_installments = self.env['dev.loan.installment']

        
    #     if wizard_id.current_month:
    #         start_current_month = today.replace(day=1)  # First day of the current month
    #         end_current_month = (start_current_month + timedelta(days=32)).replace(day=1)  # First day of the next month
    #         filtered_installments |= self.env['dev.loan.installment'].search([
    #             ('date', '>=', start_current_month),
    #             ('date', '<', end_current_month)
    #         ])
        

    #     return filtered_installments
    def get_current_installments(self, wizard_id):
        """
        Retrieves current month's installments using an SQL query.
        """
        today = fields.Date.context_today(self) 
        current_month_start = today.replace(day=1)  
        next_month_start = (current_month_start + relativedelta(months=1)).replace(day=1)  

       
        sql_query = """
            SELECT id
            FROM dev_loan_installment
            WHERE date >= %s AND date < %s
        """

       
        installment_ids = []
        if wizard_id.current_month:
            self.env.cr.execute(sql_query, (current_month_start, next_month_start))
            installment_ids = [row[0] for row in self.env.cr.fetchall()]

        
        return self.env['dev.loan.installment'].browse(installment_ids)

    # def get_next_installments(self, wizard_id):
    
    #     today = datetime.today()
    #     current_month = today.month
    #     current_year = today.year

        
    #     filtered_installments = self.env['dev.loan.installment']

        
    #     if wizard_id.next_month:
    #         start_next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)  # First day of next month
    #         end_next_month = (start_next_month + timedelta(days=32)).replace(day=1)  # First day of the month after next
    #         filtered_installments |= self.env['dev.loan.installment'].search([
    #             ('date', '>=', start_next_month),
    #             ('date', '<', end_next_month)
    #         ])
        
    #     return filtered_installments
    def get_next_installments(self, wizard_id):
        """
        Retrieves next month's installments using an SQL query.
        """
        today = fields.Date.context_today(self)  
       
        next_month_start = (today.replace(day=1) + relativedelta(months=1)).replace(day=1)
        after_next_month_start = (next_month_start + relativedelta(months=1)).replace(day=1)
    
        
        sql_query = """
            SELECT id
            FROM dev_loan_installment
            WHERE date >= %s AND date < %s
        """
    
        installment_ids = []
        if wizard_id.next_month:  
            self.env.cr.execute(sql_query, (next_month_start, after_next_month_start))
            installment_ids = [row[0] for row in self.env.cr.fetchall()]
    
        
        return self.env['dev.loan.installment'].browse(installment_ids)
    
    # def get_overdue_installments(self, wizard_id):
    
    #     today = datetime.today()
    #     current_month = today.month
    #     current_year = today.year

        
    #     filtered_installments = self.env['dev.loan.installment']
        
    #     if wizard_id.overdue_month:
    #         overdue_end = today.replace(day=1) - timedelta(days=1)  
    #         filtered_installments |= self.env['dev.loan.installment'].search([
    #             ('date', '<=', overdue_end)
    #         ])

    #     return filtered_installments

    def get_overdue_installments(self, wizard_id):
        """
        Retrieves overdue installments using an SQL query.
        """
        today = fields.Date.context_today(self)  
        overdue_end = (today.replace(day=1) - timedelta(days=1))  
    
        
        sql_query = """
            SELECT id
            FROM dev_loan_installment
            WHERE date <= %s
        """
    
        installment_ids = []
        if wizard_id.overdue_month:  
            self.env.cr.execute(sql_query, (overdue_end,))
            installment_ids = [row[0] for row in self.env.cr.fetchall()]
    
        
        return self.env['dev.loan.installment'].browse(installment_ids)
        


    
    
    def _get_report_values(self, docids, data=None):
        docs = self.env['loan.collection.wizard'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'loan.collection.wizard',
            'get_current_installments': self.get_current_installments,
            'get_next_installments': self.get_next_installments,
            'get_overdue_installments': self.get_overdue_installments,
            'docs': docs,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
