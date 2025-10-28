# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import api, fields, models, _
from datetime import datetime
import calendar
import itertools
from operator import itemgetter
import operator
from odoo.exceptions import ValidationError

class dev_update_rate(models.TransientModel):
    _name = "dev.update.rate"
    _description = 'Update Interest Rate'
    
    rate = fields.Float('Rate', required="1")
    
    def update_rate(self):
        if self.rate <= 0:
            raise ValidationError(_('Rate must be positive'))
        loan_id = self.env['dev.loan.loan'].browse(self._context.get('active_id'))
        loan_id.interest_rate = self.rate
        installment_ids = self.env['dev.loan.installment'].search([('loan_id','=',loan_id.id),('state','!=','paid')], order='date')
        last_ins_id = self.env['dev.loan.installment'].search([('loan_id','=',loan_id.id),('state','!=','paid')], order='date desc', limit=1)
        open_balance = 0
        set_open_balance = 0
        for ins in installment_ids:
            if not open_balance and not set_open_balance:
                open_balance = ins.opening_balance
                set_open_balance = True
                
            if last_ins_id.id != ins.id:
                ins.total_amount = ins.loan_id.emi_estimate
                ins.opening_balance = open_balance
                ins.closing_balance = open_balance - ins.amount
                open_balance = ins.closing_balance 
                if ins.closing_balance < 0:
                    open_balance = 0
                    ins.closing_balance = 0
                    ins.total_amount = 0
                    
                if ins.amount or ins.interest:
                    ins.total_amount = ins.amount + ins.interest
                else:
                    ins.total_amount = 0
            else:
                ins.is_last_line = True
                ins.opening_balance = open_balance
                ins.total_amount = ins.amount + ins.interest
                ins.closing_balance = ins.opening_balance - ins.amount
                if ins.closing_balance < 0:
                    ins.closing_balance = 0
                if ins.amount or ins.interest:
                    ins.total_amount = ins.amount + ins.interest
                else:
                    ins.total_amount = 0
            
            
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
    
