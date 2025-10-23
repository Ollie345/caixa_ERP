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

class generate_agreement(models.TransientModel):
    _name = "generate.agreement.wizard"
    _description = 'Generate Agreement'
    
    agreement_type_id = fields.Many2one('ln.agreement.type', string='Agreement Type')
    
    def generate_agreement(self):
        active_ids = self._context.get('active_ids')
        loan_id = self.env['dev.loan.loan'].browse(active_ids) 
        vals = {
                'partner_id': loan_id.client_id and loan_id.client_id.id  or '', 
                'agreement_type_id': self.agreement_type_id and self.agreement_type_id.id or False,
                }
        new_agreement = self.env['ln.agreement'].create(vals)
        new_agreement.loan_id=loan_id.id
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
