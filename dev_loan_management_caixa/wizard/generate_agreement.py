# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##########################################################################

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class generate_agreement(models.TransientModel):
    _name = "generate.agreement.wizard"
    _description = 'Generate Agreement'
    
    agreement_type_id = fields.Many2one('ln.agreement.type', string='Agreement Type', required=True)
    loan_id = fields.Many2one('dev.loan.loan', string='Loan')
    
    def generate_agreement(self):
        active_ids = self._context.get('active_ids')
        loan_id = self.env['dev.loan.loan'].browse(active_ids)
        
        if not loan_id:
            raise ValidationError(_("No loan selected"))
        
        if loan_id.state != 'final_approve':
            raise ValidationError(_("Loan must be in Final Approval state"))
        
        if not self.agreement_type_id:
            raise ValidationError(_("Please select an Agreement Type"))
        
        # Create agreement
        vals = {
            'partner_id': loan_id.client_id.id if loan_id.client_id else False,
            'agreement_type_id': self.agreement_type_id.id,
        }
        new_agreement = self.env['ln.agreement'].create(vals)
        new_agreement.loan_id = loan_id.id
        
        # Link agreement to loan and change state
        loan_id.write({
            'state': 'awaiting_response',
            'agreement_id': new_agreement.id,
            'customer_response': 'pending',
        })
        
        # Log agreement generation
        loan_id.message_post(
            body=_(
                "Loan agreement generated.\n"
                "Agreement: %s\n"
                "Email will be sent to customer via frontend."
            ) % new_agreement.name,
            subtype_xmlid='mail.mt_note'
        )
        
        return {
            'type': 'ir.actions.act_window_close'
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
