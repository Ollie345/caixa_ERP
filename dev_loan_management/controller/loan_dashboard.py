# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import http
from odoo.http import request
from datetime import date, timedelta
from operator import itemgetter
import itertools
import operator

class LoanDashboard(http.Controller):
    @http.route('/loan/filter', auth='public', type='json')
    def all_loan_filter(self):
        user_lst = []
        borrower_lst = []
        loan_type_lst =[]

        user_ids = request.env['res.users'].search([('share', '=', False),('company_ids','!=',False)])
        borrower_ids = request.env['res.partner'].search([('is_allow_loan','=',True)])
        loan_type_ids = request.env['dev.loan.type'].search([])

        for user_id in user_ids:
            dic = {'name': user_id.name,
                   'id': user_id.id}
            user_lst.append(dic)
        for borrower_id in borrower_ids:
            dic = {'name': borrower_id.name,
                   'id': borrower_id.id}
            borrower_lst.append(dic)
        for loan_type_id in loan_type_ids:
            dic = {'name': loan_type_id.name,
                   'id': loan_type_id.id}
            loan_type_lst.append(dic)

        return [user_lst,borrower_lst,loan_type_lst]


    @http.route('/get/loan/tiles/data', auth='public', type='json')
    def get_loan_tiles_data(self, **kwargs):
        today = date.today()
        filter_date = date.today()
        loan_aprv_domain = []
        loan_disburse_domain =[]
        loan_loan_domain = []
        loan_repayment_domain = []
        lead_domain = []
        invoice_domain = []
        loan_domain=[]
        if not kwargs.get('duration'):
            filter_date = today - timedelta(days=7)
            loan_aprv_domain = [('approve_date', '>=', filter_date), ('approve_date', '<=', today)]
            loan_disburse_domain = [('disbursement_date', '>=', filter_date), ('disbursement_date', '<=', today)]
            loan_loan_domain = [('request_date', '>=', filter_date), ('request_date', '<=', today)]
            loan_repayment_domain = [('payment_date', '>=', filter_date), ('payment_date', '<=', today)]
            invoice_domain = [('invoice_date', '>=', filter_date), ('invoice_date', '<=', today)]
            lead_domain = [('create_date', '>=', filter_date), ('create_date', '<=', today)]
        if kwargs:
            if kwargs['user_id']:
                if kwargs['user_id'] != 'all':
                    user_id = int(kwargs['user_id'])
                    loan_aprv_domain += [('user_id', '=', user_id)]
                    loan_disburse_domain += [('user_id', '=', user_id)]
                    loan_loan_domain += [('user_id', '=', user_id)]
                    loan_domain = [('user_id', '=', user_id)]
                    loan_repayment_domain += [('loan_id.user_id', '=', user_id)]
                    lead_domain += [('user_id','=',user_id)]
                    invoice_domain += [('user_id','=',user_id)]


            if kwargs['borrower_id']:
                if kwargs['borrower_id'] != 'all':
                    borrower_id = int(kwargs['borrower_id'])
                    loan_aprv_domain += [('client_id', '=', borrower_id)]
                    loan_disburse_domain += [('client_id', '=', borrower_id)]
                    loan_loan_domain += [('client_id', '=', borrower_id)]
                    loan_domain += [('client_id', '=', borrower_id)]
                    loan_repayment_domain += [('client_id', '=', borrower_id)]
                    lead_domain += [('partner_id', '=', borrower_id)]
                    invoice_domain += [('partner_id', '=', borrower_id)]
    #
            if kwargs['type_id']:
                if kwargs['type_id'] != 'all':
                    type_id = int(kwargs['type_id'])
                    loan_aprv_domain += [('loan_type_id', '=', type_id)]
                    loan_disburse_domain += [('loan_type_id', '=', type_id)]
                    loan_loan_domain += [('loan_type_id', '=', type_id)]
                    loan_domain += [('loan_type_id', '=', type_id)]
                    loan_repayment_domain += [('loan_id.loan_type_id', '=', type_id)]
                    lead_domain += [('loan_type_id', '=', type_id)]
                    invoice_domain += [('loan_id.loan_type_id', '=', type_id)]

            if kwargs['duration']:
                duration = kwargs['duration']
                if duration != 'all' and duration != 'custom_range':
                    duration = int(duration)
                    filter_date = today - timedelta(days=duration)

                    if duration == 0:
                        loan_aprv_domain += [('approve_date', '<=', filter_date),('approve_date', '>=', today)]
                        loan_disburse_domain += [('disbursement_date', '<=', filter_date),('disbursement_date', '>=', today)]
                        loan_loan_domain += [('request_date', '<=', filter_date),('request_date', '>=', today)]
                        loan_repayment_domain += [('payment_date', '>=', filter_date),('payment_date', '<=', today)]
                        invoice_domain += [('invoice_date', '>=', filter_date),('invoice_date', '<=', today)]
                        lead_domain += [('create_date', '>=', filter_date),('create_date', '<=', today)]
                    else:
                        loan_aprv_domain += [('approve_date', '>=', filter_date), ('approve_date', '<=', today)]
                        loan_disburse_domain += [('disbursement_date', '>=', filter_date),('disbursement_date', '<=', today)]
                        loan_loan_domain += [('request_date', '>=', filter_date), ('request_date', '<=', today)]
                        loan_repayment_domain += [('payment_date', '>=', filter_date), ('payment_date', '<=', today)]
                        invoice_domain += [('invoice_date', '>=', filter_date), ('invoice_date', '<=', today)]
                        lead_domain  += [('create_date', '>=', filter_date), ('create_date', '<=', today)]

                elif duration == 'custom_range':
                    # Handle custom date range
                    filter_date = kwargs.get('start_date')
                    to_date = kwargs.get('end_date')
                    if filter_date and to_date:
                        filter_date = date.fromisoformat(filter_date)
                        to_date = date.fromisoformat(to_date)
                        loan_aprv_domain += [('approve_date', '<=', filter_date), ('approve_date', '>=', today)]
                        loan_disburse_domain += [('disbursement_date', '<=', filter_date),('disbursement_date', '>=', today)]
                        loan_loan_domain += [('request_date', '>=', filter_date), ('request_date', '<=', to_date)]
                        loan_repayment_domain += [('payment_date', '>=', filter_date), ('payment_date', '<=', to_date)]
                        invoice_domain += [('invoice_date', '>=', filter_date), ('invoice_date', '<=', to_date)]
                        lead_domain += [('create_date', '>=', filter_date), ('create_date', '<=', to_date)]


        aprv_loan_amt = []
        disburse_loan_amt =[]
        paid_repayment_lst =[]
        close_loan_lst =[]
        open_close_loan_lst =[]
        total_amt_lst =[]
        all_loan_lst =[]
        all_paid_repayment_lst=[]
        total_loan_int_amt =[]
        total_interest_rate = 0.0
        invoice_price_lst =[]
        open_loan_lst = []
        ins_int_amt = []
        all_repayments= request.env['dev.loan.installment'].search(loan_repayment_domain)
        for all_payment_id in all_repayments:
            if all_payment_id.state == 'paid':
                paid_repayment_lst.append(all_payment_id.total_amount)
                ins_int_amt.append(all_payment_id.interest)
                all_paid_repayment_lst.append(all_payment_id.id)

        repayments_amt= sum(paid_repayment_lst)
        total_ins_int_amt=sum(ins_int_amt)

        # for approve loan counter
        all_aprv_loan_lst = request.env['dev.loan.loan'].search([('state','=','approve')]+loan_aprv_domain)
        for approve_loan_id in all_aprv_loan_lst:
            aprv_loan_amt.append(approve_loan_id.loan_amount)
        total_aprv_amt = sum(aprv_loan_amt)

        # for disburse loan counter
        all_disburse_lst = request.env['dev.loan.loan'].search([('state','=','disburse')]+loan_disburse_domain)
        for all_disburse_loan_id in all_disburse_lst:
            disburse_loan_amt.append(all_disburse_loan_id.loan_amount)
        total_disburse_amt = sum(disburse_loan_amt)


        # for average interest rate counter
        loan_ids = request.env['dev.loan.loan'].search(loan_domain)
        for loan_id in loan_ids:
            if loan_id.state in ['open','disburse']:
                open_loan_lst.append(loan_id.id)
                if loan_id.loan_amount > 0.0:
                    total_amt_lst.append(loan_id.loan_amount)
                    total_loan_int_amt.append(loan_id.total_interest)
            # if sum(total_amt_lst) > 0 and total_ins_int_amt != 0:
                total_interest_rate = "{:.2f}".format((sum(total_loan_int_amt) / sum(total_amt_lst)) * 100)

        all_loan_ids = request.env['dev.loan.loan'].search(loan_loan_domain)
        for loan_id in all_loan_ids:
            if loan_id.state in ['close','open']:
                open_close_loan_lst.append(loan_id.id)
            if loan_id.state == 'close':
                close_loan_lst.append(loan_id.id)


        all_loan_lead=request.env['crm.lead'].search([('loan_type_id','!=',False)]+lead_domain)
        invoice_ids = request.env['account.move'].search([('loan_id', '!=', False),('state','=','posted')]+invoice_domain)
        for invoice_id in invoice_ids:
            invoice_price_lst.append(invoice_id.invoice_line_ids.price_total)
        invoice_process_fees=sum(invoice_price_lst)
        company_currency = request.env.user.company_id.currency_id.name
        user_name = request.env.user.name
        user_img = request.env.user.image_1920


        return {
            'total_aprv_amt': total_aprv_amt,
            'all_aprv_loan_lst':all_aprv_loan_lst.ids,
            'total_disburse_amt': total_disburse_amt,
            'all_disburse_lst':all_disburse_lst.ids,
            'repayments_amt': repayments_amt,
            'paid_repayment_lst':all_paid_repayment_lst,
            'open_close_loan_lst':open_close_loan_lst,
            'close_loan_lst':close_loan_lst,
            'total_interest_rate' : total_interest_rate,
            'total_interest_lst': total_ins_int_amt,
            'all_loan_lst':all_loan_lst,
            'all_loan_lead':all_loan_lead.ids,
            'company_currency' : company_currency,
            'invoice_process_fees' : invoice_process_fees,
            'invoice_lst': invoice_ids.ids,
            'open_loan_lst' : open_loan_lst,
            'user_img': user_img,
            'user_name': user_name
        }

    # Month wise loan request
    @http.route('/month/loan/request/chart/data', auth='public', type='json')
    def get_month_wise_loan_request_chart_data(self, **kw):
        all_color_list = ['#00daa3', '#f06c67', '#0c9fa1', '#cf9ab5', '#bce459', '#3f8eae', '#ed843f', '#00c4aa',
                          '#966ca2', '#e2d65e', '#d56e80', '#c99a5c', '#61e180', '#bf784b', '#fec863', '#7269ad']
        today = date.today()

        # Calculate the start and end date for the current month and the previous 2 months
        first_day_of_current_month = today.replace(day=1)
        first_day_of_previous_month = (first_day_of_current_month - timedelta(days=1)).replace(day=1)
        first_day_of_two_months_ago = (first_day_of_previous_month - timedelta(days=1)).replace(day=1)

        start_date = first_day_of_two_months_ago  # Two months ago
        end_date = today  # Current date

        loan_domain = []
        data = kw['data']

        # Filter by user
        if data['user']:
            user_id = data['user']
            if user_id != 'all':
                user_id = int(user_id)
                loan_domain += [('user_id', '=', user_id)]

        # Filter by borrower
        if data['borrower']:
            borrower_id = data['borrower']
            if borrower_id != 'all':
                borrower_id = int(borrower_id)
                loan_domain += [('client_id', '=', borrower_id)]

        # Filter by loan type
        if data['type']:
            type_id = data['type']
            if type_id != 'all':
                type_id = int(type_id)
                loan_domain += [('loan_type_id', '=', type_id)]

        # Fetch loans from the last 3 months
        top_loan_request = request.env['dev.loan.loan'].search_read(
            [('request_date', '>=', start_date), ('request_date', '<=', end_date)] + loan_domain,
            fields=['request_date', 'loan_amount', 'name', 'id'],
            order='loan_amount desc'
        )

        # Group data by month
        n_lines = sorted(top_loan_request, key=itemgetter('request_date'))
        groups = itertools.groupby(n_lines, key=lambda x: x['request_date'].strftime('%B'))
        lines = [{'month': k, 'values': list(v)} for k, v in groups]

        # Prepare data for chart
        top_repeated_loan_req = []
        loan_req_ids_lst = []
        for line in lines:
            loan_amount = sum(loan['loan_amount'] for loan in line['values'])
            top_repeated_loan_req.append({'month': line['month'], 'loan_amount': loan_amount})
            loan_req_ids_lst.append([loan['id'] for loan in line['values']])

        # Chart data
        top_repeated_loan_req_chart = [rep_loan_data['month'] for rep_loan_data in top_repeated_loan_req]
        top_loan_req_time = [rep_loan_data['loan_amount'] for rep_loan_data in top_repeated_loan_req]

        loan_request_chart_data = {
            'labels': top_repeated_loan_req_chart,
            'datasets': [{
                'label': "Loan Amount",
                'backgroundColor': all_color_list[:len(top_repeated_loan_req_chart)],
                'data': top_loan_req_time,
                'detail': loan_req_ids_lst
            }]
        }

        return {
            'loan_request_chart_data': loan_request_chart_data
        }

    # loan collection state chart(installment chart)
    @http.route('/collection/state/chart/data', auth='public', type='json')
    def get_collection_state_chart_data(self, **kw):
            all_color_list = ['#00daa3', '#f06c67', '#0c9fa1', '#cf9ab5', '#bce459', '#3f8eae', '#ed843f', '#00c4aa',
                              '#966ca2', '#e2d65e', '#d56e80', '#c99a5c', '#61e180', '#bf784b', '#fec863', '#7269ad']
            today = date.today()
            installment_domain = []
            data = kw['data']
            if not data.get('duration'):
                filter_date = today - timedelta(days=7)
                installment_domain = [('date', '>=', filter_date), ('date', '<=', today)]

            if data['user']:
                user_id = data['user']
                if user_id != 'all':
                    user_id = int(user_id)
                    installment_domain += [('loan_id.user_id', '=', user_id)]
            if data['borrower']:
                borrower_id = data['borrower']
                if borrower_id != 'all':
                    borrower_id = int(borrower_id)
                    installment_domain += [('client_id', '=', borrower_id)]

            if data['type']:
                type_id = data['type']
                if type_id != 'all':
                    type_id = int(type_id)
                    installment_domain += [('loan_id.loan_type_id', '=', type_id)]

            if data['duration']:
                duration = data['duration']
                if duration != 'all' and duration != 'custom_range':
                    duration = int(duration)
                    filter_date = today - timedelta(days=duration)
                    if duration == 0:
                        installment_domain += [('date', '<=', today), ('date', '>=', today)]
                    else:
                        installment_domain += [('date', '>=', filter_date), ('date', '<', today)]

                elif duration == 'custom_range':
                    # Handle custom date range
                    from_date = data.get('start_date')
                    to_date = data.get('end_date')

                    if from_date and to_date:
                        from_date = date.fromisoformat(from_date)
                        to_date = date.fromisoformat(to_date)
                        installment_domain += [('date', '>=', from_date), ('date', '<=', to_date)]

            due_installment = []
            paid_installment = []
            loan_installment_ids = [[], []]
            all_installment_ids = request.env['dev.loan.installment'].search_read(installment_domain,
                                                                   fields=['name', 'client_id', 'loan_id',
                                                                           'date', 'amount', 'interest',
                                                                           'total_amount','state'],
                                                                   order="id desc")
            for installment_id in all_installment_ids:
                if (installment_id.get('state') == 'paid'):
                    paid_installment.append(installment_id)
                    loan_installment_ids[0].append(installment_id.get('id'))
                if installment_id.get('state') == 'unpaid':
                    due_installment.append(installment_id)
                    loan_installment_ids[1].append(installment_id.get('id'))

            loan_installment_chart_data = {
                'labels': ['Paid installment', 'Due installment'],
                'datasets': [{
                    'backgroundColor': all_color_list[:3],
                    'data': [len(paid_installment),len(due_installment)],
                    'detail': loan_installment_ids
                }]
            }
            return {
                'loan_installment_chart_data': loan_installment_chart_data,
            }
    # loan emi amount chart
    @http.route('/emi/amount/chart/data', auth='public', type='json')
    def get_emi_amount_chart_data(self, **kw):
            all_color_list = ['#00daa3', '#f06c67', '#0c9fa1', '#cf9ab5', '#bce459', '#3f8eae', '#ed843f', '#00c4aa',
                              '#966ca2', '#e2d65e', '#d56e80', '#c99a5c', '#61e180', '#bf784b', '#fec863', '#7269ad']
            today = date.today()
            installment_domain = []
            data = kw['data']
            if not data.get('duration'):
                filter_date = today - timedelta(days=7)
                installment_domain = [('payment_date', '>=', filter_date), ('payment_date', '<=', today)]
            if data['user']:
                user_id = data['user']
                if user_id != 'all':
                    user_id = int(user_id)
                    installment_domain += [('loan_id.user_id', '=', user_id)]
            if data['borrower']:
                borrower_id = data['borrower']
                if borrower_id != 'all':
                    borrower_id = int(borrower_id)
                    installment_domain += [('client_id', '=', borrower_id)]

            if data['type']:
                type_id = data['type']
                if type_id != 'all':
                    type_id = int(type_id)
                    installment_domain += [('loan_id.loan_type_id', '=', type_id)]

            if data['duration']:
                duration = data['duration']
                if duration != 'all' and duration != 'custom_range':
                    duration = int(duration)
                    filter_date = today - timedelta(days=duration)
                    if duration == 0:
                        installment_domain += [('payment_date', '<=', today), ('payment_date', '>=', today)]
                    else:
                        installment_domain += [('payment_date', '>=', filter_date), ('payment_date', '<=', today)]

                elif duration == 'custom_range':
                    # Handle custom date range
                    from_date = data.get('start_date')
                    to_date = data.get('end_date')
                    if from_date and to_date:
                        from_date = date.fromisoformat(from_date)
                        to_date = date.fromisoformat(to_date)
                        installment_domain += [('payment_date', '>=', from_date), ('payment_date', '<=', to_date)]

            principle_amount_lst = []
            interest_amount_lst = []
            all_paid_installment = [[],[]]
            all_installment_ids = request.env['dev.loan.installment'].search([('state', '=', 'paid')]+installment_domain)
            for installment_id in all_installment_ids:
                principle_amount_lst.append(installment_id.amount)
                interest_amount_lst.append(installment_id.interest)
                all_paid_installment[0].append(installment_id.id)
                all_paid_installment[1].append(installment_id.id)

            loan_emi_amount_chart_data = {
                'principle_amount' : sum(principle_amount_lst),
                'interest_amount' : sum(interest_amount_lst),
            }
            return {
                'loan_emi_amount_chart_data': loan_emi_amount_chart_data,
            }
    # top loan amount partner chart
    @http.route('/top/loan/amount/partner/chart/data', auth='public', type='json')
    def top_loan_amount_partner_chart(self, **kw):

        all_color_list = ['#00daa3', '#f06c67', '#0c9fa1', '#cf9ab5', '#bce459', '#3f8eae', '#ed843f', '#00c4aa',
                          '#966ca2', '#e2d65e', '#d56e80', '#c99a5c', '#61e180', '#bf784b', '#fec863', '#7269ad']

        today = date.today()
        loan_domain = []
        data = kw['data']
        if not data.get('duration'):
            filter_date = today - timedelta(days=7)
            loan_domain = [('request_date', '>=', filter_date), ('request_date', '<=', today)]

        top_partner_loan_count = data['top_partner_loan_count']
        if data['user']:
            user_id = data['user']
            if user_id != 'all':
                user_id = int(user_id)
                loan_domain += [('user_id', '=', user_id)]
        if data['borrower']:
            borrower_id = data['borrower']
            if borrower_id != 'all':
                borrower_id = int(borrower_id)
                loan_domain += [('client_id', '=', borrower_id)]

        if data['type']:
            type_id = data['type']
            if type_id != 'all':
                type_id = int(type_id)
                loan_domain += [('loan_type_id', '=', type_id)]

        if data['duration']:
            duration = data['duration']
            if duration != 'all' and duration != 'custom_range':
                duration = int(duration)
                filter_date = today - timedelta(days=duration)
                if duration == 0:
                    loan_domain += [('request_date', '<=', today),('request_date', '>=', today)]
                else:
                    loan_domain += [('request_date', '>=', filter_date), ('request_date', '<', today)]

            elif duration == 'custom_range':
                # Handle custom date range
                from_date = data.get('start_date')
                to_date = data.get('end_date')
                if from_date and to_date:
                    from_date = date.fromisoformat(from_date)
                    to_date = date.fromisoformat(to_date)
                    loan_domain += [('request_date', '>=', from_date), ('request_date', '<=', to_date)]


        top_repeated_client = []
        top_repeated_customer_chart = []
        top_partner_loan = request.env['dev.loan.loan'].search_read([('state','=','open')]+loan_domain,
                                                                  fields=['client_id', 'loan_amount'])
        filtered_loan_amount = [loan for loan in top_partner_loan if loan['client_id']]
        loan_amount_ids_lst = []
        loan_ids_lst = []
        loan_ids_sorted_list=[]
        if filtered_loan_amount:
            n_lines = sorted(filtered_loan_amount, key=itemgetter('client_id'))
            groups = itertools.groupby(n_lines, key=operator.itemgetter('client_id'))
            lines = [{'client_id': k, 'values': [x for x in v]} for k, v in groups]

            for x in lines:
                loan_amount_id_lst = []
                loan_amount_ids =[]
                for id in x['values']:
                    loan_amount_id_lst.append(id['loan_amount'])
                    loan_amount_ids.append(id['id'])
                loan_amount_ids_lst.append(sum(loan_amount_id_lst))
                loan_amount_ids_lst = sorted(loan_amount_ids_lst, reverse=True)
                loan_ids_lst.append(loan_amount_ids)
                loan_ids_sorted_list = sorted(loan_ids_lst, key=len, reverse=True)
            for line in lines:
                top_repeated_client.append(
                    {'borrower': line.get('client_id'), 'repeated_time': len(line.get('values'))})
                top_repeated_client = (sorted(top_repeated_client, key=lambda i: i['repeated_time'], reverse=True))[0:int(top_partner_loan_count)]
            for rep_customer_data in top_repeated_client:
                top_repeated_customer_chart.append(rep_customer_data.get('borrower')[1])

        partner_loan_chart_data = {
            'labels': top_repeated_customer_chart[:int(top_partner_loan_count)],
            'datasets': [{
                'label': "Top Repeated Customer",
                'backgroundColor': all_color_list[:int(top_partner_loan_count)],
                'data': loan_amount_ids_lst[:int(top_partner_loan_count)],
                'detail': loan_ids_sorted_list,
            }]
        }
        return {
            'partner_loan_chart_data': partner_loan_chart_data
        }
    # loan paid and unpaid installment chart
    @http.route('/loan/installment/chart/data', auth='public', type='json')
    def loan_installment_chart_data(self, **kw):
        data = kw['data']
        range = data['top_partner_installment_count']
        from_date = date.today()
        to_date = date.today()
        installment_domain = []
        if not data.get('duration'):
            filter_date = today - timedelta(days=7)
            installment_domain = [('request_date', '>=', filter_date), ('request_date', '<=', to_date)]

        if data['user']:
            user_id = data['user']
            if user_id != 'all':
                user_id = int(user_id)
                installment_domain += [('loan_id.user_id', '=', user_id)]
        if data['borrower']:
            borrower_id = data['borrower']
            if borrower_id != 'all':
                borrower_id = int(borrower_id)
                installment_domain += [('client_id', '=', borrower_id)]

        if data['type']:
            type_id = data['type']
            if type_id != 'all':
                type_id = int(type_id)
                installment_domain += [('loan_id.loan_type_id', '=', type_id)]

        if data['duration']:
            duration = data['duration']
            if duration != 'all' and duration != 'custom_range':
                duration = int(duration)
                filter_date = to_date - timedelta(days=duration)
                if duration == 0:
                    pass
                    # from_date = from_date
                    #
                    # installment_domain += [('payment_date', '<=', today),('payment_date', '>=', today)]
                else:
                    from_date = filter_date
                    # installment_domain += [('payment_date', '>=', filter_date), ('payment_date', '<', today)]
            #
            # elif duration == 'custom_range':
            #     # Handle custom date range
            #     from_date = data.get('start_date')
            #     to_date = data.get('end_date')
            #     if from_date and to_date:
            #         from_date = date.fromisoformat(from_date)
            #         to_date = date.fromisoformat(to_date)
            #         installment_domain += [('payment_date', '>=', from_date), ('payment_date', '<=', to_date)]

            # else:
            #     from_date = False
            #     to_date = False
        partner_lst = []
        paid_installment = []
        paid_installment_ids = []
        unpaid_installment = []
        unpaid_installment_ids = []
        query = '''
                    SELECT client_id, COUNT(*) AS installment_count FROM dev_loan_installment
                    GROUP BY client_id  ORDER BY  installment_count DESC LIMIT %s;
                    '''
        request._cr.execute(query, (range,))

        partner_ids = request._cr.fetchall()
        for partner in partner_ids:
            partner_id = request.env['res.partner'].browse(partner[0])
            if partner_id.is_allow_loan and partner_id.is_active_borrower:
                partner_lst.append(partner_id.name)
                all_installment_ids = request.env['dev.loan.installment'].search([("client_id", "=", partner_id.id), ("loan_id.state", "in", ['open', 'close'])]+installment_domain)
                paid_ids = []
                unpaid_ids = []
                for installment_id in all_installment_ids:
                    if installment_id.state == "paid" and installment_id.payment_date >= from_date and installment_id.payment_date <= to_date:
                        paid_ids.append(installment_id.id)
                    if installment_id.state == "unpaid":
                        unpaid_ids.append(installment_id.id)

                paid_installment_ids.append(paid_ids)
                paid_installment.append(len(paid_ids))
                unpaid_installment_ids.append(unpaid_ids)
                unpaid_installment.append(0 - len(unpaid_ids))

        loan_installment_chart_data= {
            'labels': partner_lst,
            'datasets': [{
                'backgroundColor': "green",
                'data': paid_installment,
                'barPercentage': 0.5,
                'label':'Paid Installment',
                },
                {
                    'backgroundColor':"red",
                    'data': unpaid_installment,
                    'barPercentage': 0.5,
                    'label': 'Unpaid Installment',
                }]
        }

        result = {
            'loan_installment_chart_data':loan_installment_chart_data
        }
        return result
    # loan type chart
    @http.route('/loan/type/chart/data', auth='public', type='json')
    def get_loan_type_chart_data(self, **kw):
        all_color_list = ['#00daa3', '#f06c67', '#0c9fa1', '#cf9ab5', '#bce459', '#3f8eae', '#ed843f', '#00c4aa',
                          '#966ca2', '#e2d65e', '#d56e80', '#c99a5c', '#61e180', '#bf784b', '#fec863', '#7269ad']
        today = date.today()
        loan_domain = []
        data = kw['data']
        if not data.get('duration'):
            filter_date = today - timedelta(days=7)
            loan_domain = [('request_date', '>=', filter_date), ('request_date', '<=', today)]

        if data['user']:
            user_id = data['user']
            if user_id != 'all':
                user_id = int(user_id)
                loan_domain += [('user_id', '=', user_id)]
        if data['borrower']:
            borrower_id = data['borrower']
            if borrower_id != 'all':
                borrower_id = int(borrower_id)
                loan_domain += [('client_id', '=', borrower_id)]

        if data['type']:
            type_id = data['type']
            if type_id != 'all':
                type_id = int(type_id)
                loan_domain += [('loan_type_id', '=', type_id)]

        if data['duration']:
            duration = data['duration']
            if duration != 'all' and duration != 'custom_range':
                duration = int(duration)
                filter_date = today - timedelta(days=duration)
                if duration == 0:
                    loan_domain += [('request_date', '<=', today),('request_date', '>=', today)]
                else:
                    loan_domain += [('request_date', '>=', filter_date), ('request_date', '<', today)]

            elif duration == 'custom_range':
                # Handle custom date range
                from_date = data.get('start_date')
                to_date = data.get('end_date')
                if from_date and to_date:
                    from_date = date.fromisoformat(from_date)
                    to_date = date.fromisoformat(to_date)
                    loan_domain += [('request_date', '>=', from_date), ('request_date', '<=', to_date)]

        loan_type_label = []
        loan_type_values = []

        loan_data = request.env['dev.loan.loan'].search_read(loan_domain,fields=['loan_type_id', 'name'])

        n_lines = sorted(loan_data, key=itemgetter('loan_type_id'))
        groups = itertools.groupby(n_lines, key=operator.itemgetter('loan_type_id'))
        lines = [{'loan_type_id': k, 'values': [x for x in v]} for k, v in groups]

        type_counting_ids = []
        for x in lines:
            type_counting_id = []
            for id in x['values']:
                type_counting_id.append(id['id'])
            type_counting_ids.append(type_counting_id)

        for line in lines:
            loan_type_label.append(line.get('loan_type_id')[1])
            loan_type_values.append(len(line.get('values')))

        loan_type_chart_data = {
            'labels': loan_type_label[:5],
            'datasets': [{
                'label': "Loan Type",
                'backgroundColor': all_color_list[:5],
                'data': loan_type_values,
                'detail': type_counting_ids
            }]
        }
        return {
            'loan_type_chart_data': loan_type_chart_data,
        }
    # upcoming installment list
    @http.route('/upcoming/installment/list/data', auth='public', type='json')
    def get_upcoming_installment_list_data(self, **kw):
        today = date.today()
        # tomorrow = today + timedelta(days=1)
        data = kw['data']
        installment_domain = []
        # User filter
        if data['user']:
            user_id = data['user']
            if user_id != 'all':
                user_id = int(user_id)
                installment_domain += [('loan_id.user_id', '=', user_id)]

        # Borrower filter
        if data['borrower']:
            borrower_id = data['borrower']
            if borrower_id != 'all':
                borrower_id = int(borrower_id)
                installment_domain += [('client_id', '=', borrower_id)]

        # Loan Type filter
        if data['type']:
            type_id = data['type']
            if type_id != 'all':
                type_id = int(type_id)
                installment_domain += [('loan_id.loan_type_id', '=', type_id)]
        if data['upc_duration']:
            duration = data['upc_duration']
            if duration == '0':
                installment_domain += [('date', '=', today)]
            elif duration.isdigit():
                days = int(duration)
                future_date = today + timedelta(days=days)
                installment_domain += [('date', '>=', today), ('date', '<=', future_date)]
        all_upcoming_installment = request.env['dev.loan.installment'].search_read(
            [('state', '=', 'unpaid')] + installment_domain,
            fields=['name', 'loan_id', 'client_id', 'amount', 'date']
        )

        return {
            'all_upcoming_installment': all_upcoming_installment
        }
    # overdue installment list
    @http.route('/overdue/installment/list/data', auth='public', type='json')
    def get_overdue_installment_list_data(self, **kw):
        today = date.today()
        data = kw['data']
        installment_domain = []
        if not data.get('duration'):
            installment_domain = [('request_date', '<', today)]

        if data['user']:
            user_id = data['user']
            if user_id != 'all':
                user_id = int(user_id)
                installment_domain += [('loan_id.user_id', '=', user_id)]
        if data['borrower']:
            borrower_id = data['borrower']
            if borrower_id != 'all':
                borrower_id = int(borrower_id)
                installment_domain += [('client_id', '=', borrower_id)]

        if data['type']:
            type_id = data['type']
            if type_id != 'all':
                type_id = int(type_id)
                installment_domain += [('loan_id.loan_type_id', '=', type_id)]

        if data['duration']:
            duration = data['duration']
            if duration == 'all':
                installment_domain += [('date', '<', today)]
            elif duration != 'all' and duration != 'custom_range':
                duration = int(duration)
                filter_date = today - timedelta(days=duration)
                if duration == 0:
                    installment_domain += [('date', '<', today)]
                else:
                    installment_domain += [('date', '>=', filter_date), ('date', '<', today)]

            elif duration == 'custom_range':
                # Handle custom date range
                from_date = data.get('start_date')
                to_date = data.get('end_date')
                if from_date and to_date:
                    from_date = date.fromisoformat(from_date)
                    to_date = date.fromisoformat(to_date)
                    installment_domain += [('date', '>=', from_date), ('date', '<=', to_date)]
        all_overdue_installment = request.env['dev.loan.installment'].search_read([('state','=','unpaid')]+installment_domain,
                                                                                   fields=['name', 'loan_id',
                                                                                           'client_id',
                                                                                           'amount', 'date'])
        return {
            'all_overdue_installment': all_overdue_installment
        }

    # loan state wise chart

    @http.route('/loan/state/wise/chart/data', auth='public', type='json')
    def get_loan_state_wise_chart_data(self, **kw):
            all_color_list = ['#00daa3', '#f06c67', '#0c9fa1', '#cf9ab5', '#bce459', '#3f8eae', '#ed843f', '#00c4aa',
                              '#966ca2', '#e2d65e', '#d56e80', '#c99a5c', '#61e180', '#bf784b', '#fec863', '#7269ad']
            today = date.today()
            loan_domain = []
            data = kw['data']
            if not data.get('duration'):
                filter_date = today - timedelta(days=7)
                loan_domain = [('request_date', '>=', filter_date), ('request_date', '<=', today)]

            if data['user']:
                user_id = data['user']
                if user_id != 'all':
                    user_id = int(user_id)
                    loan_domain += [('user_id', '=', user_id)]
            if data['borrower']:
                borrower_id = data['borrower']
                if borrower_id != 'all':
                    borrower_id = int(borrower_id)
                    loan_domain += [('client_id', '=', borrower_id)]

            if data['type']:
                type_id = data['type']
                if type_id != 'all':
                    type_id = int(type_id)
                    loan_domain += [('loan_type_id', '=', type_id)]

            if data['duration']:
                duration = data['duration']
                if duration != 'all' and duration != 'custom_range':
                    duration = int(duration)
                    filter_date = today - timedelta(days=duration)
                    if duration == 0:
                        loan_domain += [('request_date', '<=', today), ('request_date', '>=', today)]
                    else:
                        loan_domain += [('request_date', '>=', filter_date), ('request_date', '<', today)]

                elif duration == 'custom_range':
                    # Handle custom date range
                    from_date = data.get('start_date')
                    to_date = data.get('end_date')
                    if from_date and to_date:
                        from_date = date.fromisoformat(from_date)
                        to_date = date.fromisoformat(to_date)
                        loan_domain += [('request_date', '>=', from_date), ('request_date', '<=', to_date)]

            draft_loan = []
            confirm_loan  = []
            approve_loan = []
            disburse_loan = []
            open_loan =[]
            close_loan =[]
            loan_ids = [[],[],[],[],[],[]]
            all_loan_ids = request.env['dev.loan.loan'].search_read(loan_domain,
                                                                   fields=['name', 'client_id', 'loan_type_id',
                                                                           'request_date', 'loan_amount', 'interest_rate',
                                                                           'state'],
                                                                   order="id desc")
            for all_loan_id in all_loan_ids:
                if (all_loan_id.get('state') == 'draft'):
                    draft_loan.append(all_loan_id)
                    loan_ids[0].append(all_loan_id.get('id'))
                if all_loan_id.get('state') == 'confirm':
                    confirm_loan.append(all_loan_id)
                    loan_ids[1].append(all_loan_id.get('id'))
                if all_loan_id.get('state') == 'approve':
                    approve_loan.append(all_loan_id)
                    loan_ids[2].append(all_loan_id.get('id'))
                if all_loan_id.get('state') == 'disburse':
                    disburse_loan.append(all_loan_id)
                    loan_ids[3].append(all_loan_id.get('id'))
                if all_loan_id.get('state') == 'open':
                    open_loan.append(all_loan_id)
                    loan_ids[4].append(all_loan_id.get('id'))
                if all_loan_id.get('state') == 'close':
                    close_loan.append(all_loan_id)
                    loan_ids[5].append(all_loan_id.get('id'))

            loan_state_wise_chart_data = {
                'labels': ['Draft', 'Confirm','Approve','Disburse','Open','Close'],
                'datasets': [{
                    'backgroundColor': all_color_list[:],
                    'data': [len(draft_loan),len(confirm_loan),len(approve_loan),len(disburse_loan),len(open_loan),len(close_loan)],
                    'detail': loan_ids
                }]
            }
            return {
                'loan_state_wise_chart_data': loan_state_wise_chart_data,
            }


    @http.route('/loan/filter-apply', auth='public', type='json')
    def loan_filter_apply(self, **kw):
        data = kw['data']
        user_id = data['user']
        borrower_id = data['borrower']
        type_id = data['type']
        duration = data['duration']
        start_date = data['start_date']
        end_date = data['end_date']

        result = self.get_loan_tiles_data(
            user_id=user_id,borrower_id=borrower_id,type_id=type_id,duration=duration,start_date=start_date,end_date=end_date)
        return result
