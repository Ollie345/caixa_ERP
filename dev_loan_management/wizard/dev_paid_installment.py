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

class dev_paid_installment(models.TransientModel):
    _name = "dev.paid.installment"
    _description = 'Paid Installment'
    
    opening_balance = fields.Float('Opening Balance', required="1")
    principal_amount = fields.Float('Principal Amount', required="1")
    interest_amount = fields.Float('Interest Amount', required="1")
    emi_amount =fields.Float('EMI', required="1")
    paid_amount = fields.Float('Paid Amount', required="1")
    closing_amount = fields.Float('Closing Amount', required="1")
    
    
    def paid_installment(self):
        installment_pool = self.env['dev.loan.installment']
        active_id =self._context.get('active_id')
        obj = installment_pool.browse(active_id)
        if self.paid_amount <= self.interest_amount:
            raise ValidationError(_('Paid Amount Must be greater then Interest Amount'))
        
        obj.total_amount = self.paid_amount
        obj.closing_balance = obj.opening_balance - obj.amount
        obj.action_paid_installment()
        if self.paid_amount > self.emi_amount:
            installment_ids = installment_pool.search([('loan_id','=',obj.loan_id.id),('state','!=','paid')], order='date')
            last_ins_id = installment_pool.search([('loan_id','=',obj.loan_id.id),('state','!=','paid')], order='date desc', limit=1)
            opening_balance = obj.closing_balance
            for ins in installment_ids:
                if ins.id != last_ins_id.id:
                    if opening_balance <= 0:
                        ins.total_amount = 0
                        ins.write({
                            'opening_balance':0,
                            'closing_balance':0,
                        })
                        opening_balance = 0
                    else:
                        ins.write({
                            'opening_balance':opening_balance,
                            'closing_balance':opening_balance - ins.amount,
                        })
                        if ins.closing_balance < 0:
                            ins.closing_balance = 0
                            ins.total_amount = ins.amount + ins.interest
                        opening_balance = ins.closing_balance
                else:
                    ins.is_last_line = True
                    ins.opening_balance = opening_balance
                    ins.total_amount = ins.amount + ins.interest
                    ins.closing_balance = ins.opening_balance - ins.total_amount
                    if ins.closing_balance < 0:
                        ins.closing_balance = 0
        return True
            
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
    
