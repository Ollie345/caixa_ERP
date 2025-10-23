# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import models


class LoanAccountSummary(models.AbstractModel):

    _name = 'report.dev_loan_management.hotel_booking_history_tmpl'

    # def get_booking_details(self, wizard_id):
    #     booking_ids = self.env['dev.book.hotel'].search([('date', '>=', wizard_id.start_date),
    #                                            ('date', '<=', wizard_id.end_date),
    #                                            ('hotel_id', '=', wizard_id.hotel_id.id)])
    #     if booking_ids:
    #         return booking_ids
    #     else:
    #         return False

    def _get_report_values(self, docids, data=None):
        docs = self.env['dev.loan.account.summary'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'dev.loan.account.summary',
            # 'get_booking_details': self.get_booking_details,
            'docs': docs,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
