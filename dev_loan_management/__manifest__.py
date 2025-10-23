# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

{
    'name': 'Loan Management System in Odoo for Customer and Supplier | Customer Loan | Supplier Loan',
    'version': '18.0.1.1',
    'sequence': 1,
    'category': 'Services',
    'description':
        """
This Module help to create loan of customer or Supplier
Customer Supplier loan management
Odoo Customer Supplier loan management
Customer Supplierloan
Odoo Customer Supplier loan
loan for Customer Supplier
Customer Supplier loan approval functionality 
Loan Installment link with Customer Supplier
Loan notification Customer/Supplier Inbox
Loan Deduction in Customer/Supplier
Manage Customer/Supplier loan 
Manage Customer/Supplier loan odoo
Manage loan for Customer/Supplier
Manage loan for Customer/Supplier odoo
Loan management 
Odoo loan management
Odoo loan management system
Odoo loan management app
helps you to create customized loan
 module allow Manager to manage loan of Customer/Supplier
Loan Request and Approval
Odoo Loan Report
create different types of loan for Customer/Supplier
allow user to configure loan given to Customer/Supplier will be interest payable or not.
Open Customer/Supplier Loan Management
Loan accounting
Odoo loan accounting
Customer/Supplier can create loan request.
Manage Customer/Supplier Loan and Integrated with Accouting  
Customer loan management 
Odoo customer loan management 
Supplier loan management 
Odoo supplier loan management 
Manage loan management 
Manage customer loan management
Odoo manage loan management
Odoo manage customer loan management 
Easy loan management workflow Define Loan Type
Manage supplier loan management 
Odoo manage supplier loan management 
Odoo Easy loan management workflow Define Loan Type
Add different loan types
Odoo Add different loan types
Add Loan Proofs or Required Documents List
Odoo Add Loan Proofs or Required Documents List
Loan Account Based on Loan Type
Odoo Loan Account Based on Loan Type
Send Confirmation Notification to Loan Manager
Odoo Send Confirmation Notification to Loan Manager
Manager can Approve Loan Request
Odoo Manager can Approve Loan Request
 Loan PDF Report
Odoo  Loan PDF Report
Manage  Loan PDF Report
Odoo manage  Loan PDF Report
Loan Summary PDF Report
Odoo Loan Summary PDF Report
Manage Loan Summary PDF Report
Odoo manage Loan Summary PDF Report
odoo app manage Customer / Supplier Loan Management, Customer Loan, Supplier Loan, vendor Loan, Loan Type, Loan Proef, Loan type, Loan Request, Notification, Loan Document, Loan installment, Loan Disbursement, Customer Loan Process, Loan emi
Loan Management system in odoo for customer and supplier, Customer Loan, Supplier Loan, vendor Loan, Loan Type, Loan Proef, Loan type, Loan Request, Notification, Loan Document, Loan installment, Loan Disbursement, Customer Loan Process, Loan emi, Loan summary report

    """,
    'summary': 'Loan Management system in odoo for customer and supplier Customer Loan Supplier Loan vendor Loan Loan Type Loan Proef Loan type Loan Request Notification Loan Document Loan installment Loan Disbursement Customer Loan Process Loan emi Loan summary report Loan Ouststanding Report',
    'depends': ['crm','mail','account','project'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/demo_data.xml',
        'data/cron.xml',
        'edi/mail_template.xml',
        'views/dev_loan_menu.xml',
        'wizard/dev_paid_installment_views.xml',
        'wizard/dev_update_rate_views.xml',
        'wizard/add_advance_payment_views.xml',
        'wizard/generate_agreement.xml',
        'views/dev_loan_proof_view.xml',
        'views/dev_loan_type.xml',
        'views/res_partner_view.xml',
        'wizard/dev_loan_reject_view.xml',
        'wizard/dev_installment_summary_views.xml',
        'wizard/dev_interest_certificate_views.xml',
        'wizard/create_task.xml',
        'wizard/generate_notice.xml',
        'views/dev_loan_view.xml',
        'views/dev_loan_installment_view.xml',
        'report/report_header.xml',
        'report/report_print_loan.xml',
        'report/installment_summary_template.xml',
        'report/interest_certificate_template.xml',
        'report/outstanding_letter_template.xml',
        'report/report_menu.xml',
        'views/borrower_category.xml',
        'views/dev_loan_over_due_installment_view.xml',
        'views/ln_base_document.xml',
        'views/ln_document_type.xml',
        'views/loan_checklist_template.xml',
        'views/co_borrower_relation.xml',
        'views/agreement_type.xml',
        'views/loan_agreement.xml',
        'views/agreement_template.xml',
        'report/report_agreement_template.xml',
        'data/agreement_email.xml',
        'wizard/loan_collection.xml',
        'report/loan_collection_template.xml',
        'wizard/dev_loan_account_summary.xml',
        'views/notice_type.xml',
        'views/loan_notice.xml',
        'views/dev_loan_eligibility_view.xml',
        'data/notice_email.xml',
        'report/report_notice_template.xml',
        'data/overdue_installment_email.xml',
        'views/reminder_days_view.xml',
        'views/crm_lead.xml',
        'views/loan_dashboard.xml',
        'data/restructure_sequence.xml',
        'views/dev_loan_restructure_views.xml',
        'wizard/dev_loan_restructure_wizard.xml',
          
        ],
    'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.gif'],
    'installable': True,
    'application': True,
    'auto_install': False,
    
    # author and support Details =============#
    'author': 'DevIntelle Consulting Service Pvt.Ltd',
    'website': 'https://www.devintellecs.com',    
    'maintainer': 'DevIntelle Consulting Service Pvt.Ltd', 
    'support': 'devintelle@gmail.com',
    'price':119.0,
    'currency':'EUR',
    #'live_test_url':'https://youtu.be/A5kEBboAh_k',
    'pre_init_hook' :'pre_init_check',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
