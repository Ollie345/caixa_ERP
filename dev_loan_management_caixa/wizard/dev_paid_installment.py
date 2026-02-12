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
from odoo.exceptions import ValidationError

class dev_paid_installment(models.TransientModel):
    _name = "dev.paid.installment"
    _description = 'Paid Installment'
    
    opening_balance = fields.Float('Opening Balance', required="1")
    principal_amount = fields.Float('Principal Amount', required="1")
    interest_amount = fields.Float('Interest Amount', required="1")
    penalty_amount = fields.Float('Penalty Amount', readonly=True)
    emi_amount = fields.Float('EMI', required="1")
    paid_amount = fields.Float('Paid Amount', required="1")
    closing_amount = fields.Float('Closing Amount', required="1")
    days_elapsed = fields.Integer('Days Elapsed', readonly=True)
    
    @api.model
    def default_get(self, fields_list):
        """Pro-rate interest based on days elapsed and calculate paid_amount including penalty"""
        res = super().default_get(fields_list)
        active_id = self._context.get('active_id')
        if active_id:
            installment = self.env['dev.loan.installment'].browse(active_id)
            loan = installment.loan_id
            penalty = installment.penalty_amount or 0.0
            res['penalty_amount'] = penalty
            
            # --- PRO-RATE INTEREST BASED ON DAYS ELAPSED ---
            today = fields.Date.today()
            
            # Find last payment reference date
            paid_installments = self.env['dev.loan.installment'].search([
                ('loan_id', '=', loan.id),
                ('state', '=', 'paid')
            ], order='date desc', limit=1)
            
            if paid_installments:
                last_payment_date = paid_installments.date
            else:
                # First installment: use disbursement date
                last_payment_date = loan.disbursement_date
            
            # Calculate days elapsed (min 1, max 30)
            if last_payment_date:
                days_elapsed = (today - last_payment_date).days
                days_elapsed = min(max(days_elapsed, 1), 30)
            else:
                days_elapsed = 30  # Fallback to full month
            
            res['days_elapsed'] = days_elapsed
            
            # Pro-rate interest using daily_interest (interest / 30)
            full_interest = installment.interest or 0.0
            daily_rate = full_interest / 30 if full_interest else 0.0
            pro_rated_interest = round(daily_rate * days_elapsed, 2)
            
            # Principal stays the same from the schedule
            principal = installment.amount or 0.0
            
            # Override wizard defaults with pro-rated values
            res['opening_balance'] = installment.opening_balance or 0.0
            res['principal_amount'] = principal
            res['interest_amount'] = pro_rated_interest
            res['emi_amount'] = principal + pro_rated_interest
            res['closing_amount'] = installment.closing_balance or 0.0
            res['paid_amount'] = principal + pro_rated_interest + penalty
            
        return res
    
    def paid_installment(self):
        installment_pool = self.env['dev.loan.installment']
        active_id = self._context.get('active_id')
        obj = installment_pool.browse(active_id)
        
        # Calculate minimum payment including penalty
        minimum_payment = self.interest_amount + (self.penalty_amount or 0.0)
        if self.paid_amount <= minimum_payment:
            raise ValidationError(_('Paid Amount Must be greater than Interest + Penalty Amount'))
        
        # Store pro-rated interest BEFORE action_paid_installment
        # This ensures journal entries use the correct pro-rated interest
        obj.paid_interest = self.interest_amount
        obj.total_amount = self.paid_amount
        obj.closing_balance = obj.opening_balance - self.principal_amount
        
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
    
