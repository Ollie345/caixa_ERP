# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import fields, models,api,_

class account_move(models.Model):
    _inherit = 'account.move'

    # Rename to avoid clashing with Enterprise account_loans.related field
    loan_ref_id = fields.Many2one('dev.loan.loan', string='Loan')
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
