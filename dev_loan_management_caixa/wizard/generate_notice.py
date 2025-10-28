# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##########################################################################

from odoo import fields, models,api

class generate_notice(models.TransientModel):
    _name = "generate.notice.wizard"
    _description = 'Generate Notice'
    
    notice_type_id = fields.Many2one('ln.notice.type', string='Notice Type')
    
    def generate_notice(self):
        active_ids = self._context.get('active_ids')
        loan_id = self.env['dev.loan.loan'].browse(active_ids) 
        vals = {
                'partner_id': loan_id.client_id and loan_id.client_id.id  or '', 
                'notice_type_id': self.notice_type_id and self.notice_type_id.id or False,
                }
        new_notice = self.env['ln.notice'].create(vals)
        new_notice.loan_id=loan_id.id
        print('=====================================')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
