# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class dev_loan_loan(models.Model):
    _name = 'dev.loan.loan'
    _inherit = 'dev.loan.loan'

    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % (_('Loan'), self.name)
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
