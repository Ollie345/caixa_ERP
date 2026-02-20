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
    agreement_template_id = fields.Many2one('agreement.template', string='Agreement Template')
    description = fields.Html('Description')
    loan_id = fields.Many2one('dev.loan.loan', string='Loan')
    
    @api.onchange('agreement_template_id')
    def onchange_agreement_template_id(self):
        if self.agreement_template_id:
            # Fetch the template description with placeholders
            template_description = self.agreement_template_id.description or ""
            
            if 'Desclaimer' in template_description:
                main_content = template_description.split("Desclaimer")[0].strip()
            else:
                main_content = template_description
            
            # Initialize dynamic values with defaults
            dynamic_values = {
                'name': '',
                'loan_type': '',
                'loan_amount': '0.00',
                'loan_term': '',
            }
            
            # Use loan data from context or field
            loan = self.loan_id
            if not loan and self._context.get('active_id'):
                loan = self.env['dev.loan.loan'].browse(self._context.get('active_id'))

            # Populate dynamic values
            if loan:
                if loan.client_id:
                    dynamic_values['name'] = loan.client_id.name
                if loan.loan_type_id:
                    dynamic_values['loan_type'] = loan.loan_type_id.name
                if loan.loan_amount:
                    dynamic_values['loan_amount'] = f"{loan.loan_amount:,.2f}"
                if loan.loan_term:
                    dynamic_values['loan_term'] = str(loan.loan_term)
            
            # Update the description by formatting with dynamic values
            # We reuse the helper from ln.agreement if possible, or reimplement
            import re
            placeholder_pattern = r'{(\w+)}'
            self.description = re.sub(
                placeholder_pattern,
                lambda match: dynamic_values.get(match.group(1), match.group(0)),
                main_content or ""
            )

    
    def generate_agreement(self):
        active_ids = self._context.get('active_ids')
        loan_id = self.env['dev.loan.loan'].browse(active_ids)
        
        if not loan_id:
            loan_id = self.loan_id
            
        if not loan_id or not loan_id.exists():
            raise ValidationError(_("No loan selected or loan record not found."))
        
        if loan_id.state not in ['final_approve', 'under_review']:
            raise ValidationError(_("Loan must be in 'Final Approval' or 'Under Review' state to generate an agreement."))
        
        if not self.agreement_type_id:
            raise ValidationError(_("Please select an Agreement Type"))
        
        # Create agreement
        vals = {
            'partner_id': loan_id.client_id.id if loan_id.client_id else False,
            'agreement_type_id': self.agreement_type_id.id,
            'agreement_template_id': self.agreement_template_id.id,
            'description': self.description,
        }
        new_agreement = self.env['ln.agreement'].create(vals)
        new_agreement.loan_id = loan_id.id
        
        # Link agreement to loan and change state
        is_revision = self._context.get('is_revision')
        write_vals = {
            'state': 'awaiting_response',
            'agreement_id': new_agreement.id,
            'customer_response': 'pending',
            'customer_response_date': False,
        }
        
        loan_id.write(write_vals)
        
        # Log agreement generation
        log_msg = _(
            "Loan agreement generated.\n"
            "Agreement: %s\n"
            "Email will be sent to customer via frontend."
        ) % new_agreement.name
        
        if is_revision:
            log_msg = _("Revised ") + log_msg
            if loan_id.revision_count > 0:
                log_msg += _("\nRevision #%s") % loan_id.revision_count
        
        loan_id.message_post(
            body=log_msg,
            subtype_xmlid='mail.mt_note'
        )

        loan_id._notify_frontend(
            "Agreement Sent", 
            "Loan Agreement Ready", 
            _("Your loan agreement for %s is ready. Please review and sign it in your dashboard.") % (loan_id.name)
        )
        
        return {
            'type': 'ir.actions.act_window_close'
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
