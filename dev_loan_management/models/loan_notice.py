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


class LoanNotice(models.Model):
    _name = "ln.notice"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _description = "Loan Notice"

    name = fields.Char('Name', default='/', copy=False)
    partner_id = fields.Many2one('res.partner', domain=[('is_allow_loan','=',True)], required="1", string='Borrower')
    notice_type_id = fields.Many2one('ln.notice.type', string='Notice Type')
    notice_template_id = fields.Many2one('agreement.template', string='Notice Template')
    loan_id = fields.Many2one('dev.loan.loan', string='Loan')
    description=fields.Html('Description')                          
    color=fields.Integer('Color')
    header = fields.Char(string="Header")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self:self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self:self.env.user.company_id.currency_id.id)

    def _compute_access_url(self):
        super(LoanNotice, self)._compute_access_url()
        for loan in self:
            loan.access_url = '/my/loan_notice/%s' % (loan.id)

    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % (_('Loan'), self.name)
            
    @api.model
    def create(self,vals):
        vals.update({
                    'name':self.env['ir.sequence'].next_by_code('dev.loan.notice') or _('/')
                })
        return super(LoanNotice,self).create(vals)
        

    def _replace_placeholders(self, text, values):
        """
        Replace placeholders in the text with corresponding values from the dictionary.
        """
        import re
        placeholder_pattern = r'{(\w+)}'  # Matches {placeholder_name}
        return re.sub(
            placeholder_pattern,
            lambda match: values.get(match.group(1), match.group(0)),  # Replace or keep the placeholder
            text or ""
        )
        
    @api.onchange('notice_template_id')
    def onchange_notice_template_id(self):
        if self.notice_template_id:
            # Fetch the template description with placeholders
            template_description = self.notice_template_id.description or ""
            
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
            
            # Populate dynamic values if partner_id is set
            if self.partner_id:
                dynamic_values['name'] = self.partner_id.name
            
            # Populate dynamic values if loan_id is set
            if self.loan_id:
                if self.loan_id.loan_type_id:
                    dynamic_values['loan_type'] = self.loan_id.loan_type_id.name
                if self.loan_id.loan_amount:
                    dynamic_values['loan_amount'] = f"{self.loan_id.loan_amount:,.2f}"
                if self.loan_id.loan_term:
                    dynamic_values['loan_term'] = str(self.loan_id.loan_term)
            
            # Update the description by formatting with dynamic values
            self.description = self._replace_placeholders(main_content, dynamic_values)
    
        
    def send_by_mail(self):
        
        self.ensure_one()
        template_id = self.env.ref('dev_loan_management.template_notice_send_by_mail')
        ctx = {
            'default_model': 'ln.notice',
            'default_res_ids': self.ids,
            'default_template_id': template_id and template_id.id or False,
            'default_composition_mode': 'comment',
            'force_email': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
