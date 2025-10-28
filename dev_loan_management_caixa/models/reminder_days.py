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


class reminder_days(models.Model):
    _name = "reminder.days"
    _description = "Installment Reminder Days"
    _rec_name='days_before_due'
    
    days_before_due = fields.Integer(string="Days Before Due")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
