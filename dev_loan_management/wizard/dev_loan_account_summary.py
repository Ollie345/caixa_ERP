# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import fields, models, api, _
from datetime import date
from odoo.tools.misc import xlwt
from io import BytesIO
import base64
from xlwt import easyxf
from datetime import datetime
from odoo.exceptions import ValidationError


class LOANACCOUNTSUMMARY(models.TransientModel):
    _name = "dev.loan.account.summary"
    _description = "Loan Account Summary"

    loan_status = fields.Selection([('draft','Draft'),
                              ('confirm','Confirm'),
                              ('approve','Approve'),
                              ('disburse','Disburse'),
                              ('open','Open'),
                              ('close','Close'),
                              ('cancel','Cancel'),
                              ('reject','Reject')], string="Status" , required='1',default='draft')

    customer_select=fields.Selection([('all','ALL'),('selected_customer','Selected Customer')], default='all',string='Customer Select' )

    customer_ids = fields.Many2many('res.partner' ,string='Select Customer')

    company_id = fields.Many2one('res.company', string='Company', default=lambda self:self.env.user.company_id.id)


    @api.constrains('customer_select', 'customer_ids')
    def _check_customer_ids(self):
        for record in self:
            if record.customer_select == 'selected_customer' and not record.customer_ids:
                raise ValidationError("Please select at least one customer when 'Selected Customers' is chosen.")


    def excel_loan_account_summary(self):

        state_mapping = {
    'draft': 'Draft',
    'confirm':'Confirm',
    'approve': 'Approve',
    'disburse':'Disburse',
    'open':'Open',
    'close':'Close',
    'cancel':'Cancel',
    'reject':'Reject',
    
}


        domain = []
        if self.loan_status:
            domain.append(('state', '=', self.loan_status))
        if self.customer_select == 'selected_customer' and self.customer_ids:
            domain.append(('client_id', 'in', self.customer_ids.ids))
        
        
        loan_account_ids = self.env['dev.loan.loan'].search(domain)

        grouped_loans = {}
        for loan in loan_account_ids:
            grouped_loans.setdefault(loan.client_id.name, []).append(loan)


        workbook = xlwt.Workbook()
        content = easyxf('font:height 200;')
        header_style = easyxf('font:height 200;pattern: pattern solid, fore_color 0x3F; align: horiz center;font:bold True;')
        
        worksheet = workbook.add_sheet( 'Loan Account History',cell_overwrite_ok=True)
        worksheet.col(0).width = 4500
        worksheet.col(1).width = 4500
        worksheet.col(2).width = 4500
        worksheet.col(3).width = 4500
        worksheet.col(4).width = 4500
        worksheet.col(5).width = 4500
        worksheet.col(6).width = 4500
        worksheet.col(7).width = 4500
        counter = 3

        header_style = easyxf('font:height 350;pattern: pattern solid, fore_color 0x18; align: horiz center; align: vert center; font:bold True;')
        sub_header = easyxf('font:height 210;pattern: pattern solid, fore_color 0x1F;font:bold True;')
        sub_header_customer= easyxf('font:height 250;pattern: pattern solid, fore_color 0x3A; align: vert center; font:bold True;')
        content = easyxf('font:height 200;')
        content_not = easyxf('font:height 200;font:italic True;')
        content_section = easyxf('font:height 210;pattern: pattern solid, fore_color gray25;font:bold True;')
        content1_amount = easyxf('font:height 200; align: horiz right;  ')
        content_amount = easyxf('font:height 200; font:bold True; pattern: pattern solid, fore_color gray25; align: horiz right;  ')
        content_right = easyxf('font:height 200; align: horiz right;')
        
        
        heading = f"Company : {self.company_id.name}"
        worksheet.write_merge(counter-1,counter+1,0,7,heading, header_style)


        counter += 3

        for customer_name, loans in grouped_loans.items():
            # Write customer-specific header
            worksheet.write_merge(counter, counter+1, 0, 7, f"Customer: {customer_name}", sub_header_customer)
            counter += 2

            # Table headers for each customer
            headers = ['Name', 'Loan Date', 'Phone Number', 'Loan Amount', 'Interest Amount', 'Paid Amount', 'Remaining Amount', 'Status']
            for col_num, header in enumerate(headers):
                worksheet.write(counter, col_num, header, sub_header)
            counter += 1

            # Write customer's loan data
            for loan in loans:
                worksheet.write(counter, 0, loan.client_id.name, content)
                worksheet.write(counter, 1, loan.request_date.strftime('%Y-%m-%d') if loan.request_date else '', content)
                worksheet.write(counter, 2, loan.client_id.phone or '', content)
                worksheet.write(counter, 3, '\u20B9{:,.2f}'.format(loan.loan_amount), content_right)
                worksheet.write(counter, 4, '\u20B9{:,.2f}'.format(loan.total_interest), content_right)
                worksheet.write(counter, 5, '\u20B9{:,.2f}'.format(loan.paid_amount), content_right)
                worksheet.write(counter, 6, '\u20B9{:,.2f}'.format(loan.remaing_amount), content_right)
                state_label = state_mapping.get(loan.state, 'Unknown')
                worksheet.write(counter, 7, state_label, content)
                counter += 1

                paid_installments = loan.installment_ids.filtered(lambda i: i.state == 'paid')
                if paid_installments:
                    # Write Installment Header
                    installment_headers = ['Name', 'Date', 'Principal Amount', 'Interest Amount', 'EMI']
                    for col_num, header in enumerate(installment_headers):
                        worksheet.write(counter, col_num, header, sub_header)
                    counter += 1

                    for installment in paid_installments:
                        worksheet.write(counter, 0, installment.name, content)
                        worksheet.write(counter, 1, installment.date.strftime('%Y-%m-%d') if installment.date else '', content)
                        worksheet.write(counter, 2, '\u20B9{:,.2f}'.format(installment.amount), content_right)
                        worksheet.write(counter, 3, '\u20B9{:,.2f}'.format(installment.interest), content_right)
                        worksheet.write(counter, 4, '\u20B9{:,.2f}'.format(installment.total_amount) or '', content_right)
                        counter += 1
                counter +=1

            # Add spacing between customers
            counter += 2

    
        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        excel_file = base64.encodebytes(fp.read())
        fp.close()
        self.write({'excel_file': excel_file})
        active_id = self.ids[0]
        url = ('web/content/?model=dev.loan.account.summary&download=true&field=excel_file&id=%s&filename=%s' % (active_id, 'Loan Account Summary.xls'))
        if self.excel_file:
            return {'type': 'ir.actions.act_url',
                    'url': url,
                    'target': 'new'}

    excel_file = fields.Binary('Excel File')



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:



    
    
    
    
