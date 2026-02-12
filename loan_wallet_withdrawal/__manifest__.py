# -*- coding: utf-8 -*-
{
    'name': 'Loan Wallet Withdrawal',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Handle withdrawal requests from customer wallet accounts',
    'description': """
Loan Wallet Withdrawal Module
=============================
This module handles withdrawal requests from customer wallet accounts to their bank accounts.

Features:
---------
* Customer withdrawal request form
* Approval workflow (Draft → Approval → Done)
* Mandatory transaction ID before completion
* Links to loan management and customer profiles
* Track withdrawal history per customer
    """,
    'author': 'Olayinka Segun',
    'website': 'https://github.com/Olayinka-Segun',
    'depends': [
        'account',
        'dev_loan_management_caixa',
        'rest_api_odoo',  # For wallet integration
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence.xml',
        'views/loan_wallet_withdrawal_views.xml',
        'views/loan_wallet_withdrawal_reject_wizard_views.xml',
        'views/res_partner_views.xml',
        'views/dev_loan_loan_views.xml',
        'data/menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
