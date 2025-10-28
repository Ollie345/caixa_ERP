# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import fields, models


class IrAttachement(models.Model):
    _inherit = 'ir.attachment'

    loan_id = fields.Many2one('dev.loan.loan',string='Loan',copy=False)
    co_borrower_id = fields.Many2one('dev.loan.loan',string='Loan',copy=False)
    document_type = fields.Selection([
        ('loan', 'Loan Document'),
        ('co_borrower', 'Co-Borrower Document'),
    ], string="Document Type")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
