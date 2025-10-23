/** @odoo-module */
//import { registry } from '@web/core/registry';
//const { Component, onWillStart, onMounted, useState, useRef } = owl
//import { useService } from "@web/core/utils/hooks";
//import { jsonrpc } from "@web/core/network/rpc_service";
//import { _t } from "@web/core/l10n/translation";
//import { loadJS } from "@web/core/assets";
import { registry } from '@web/core/registry';
const { Component, onWillStart, onMounted, useState, useRef } = owl
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { loadJS } from "@web/core/assets";
 import { _t } from "@web/core/l10n/translation";

export class LoanDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.rpc = this.env.services.rpc
        this.state = useState({
            total_aprv_amount: 0,
            total_disburse_amt : 0,
            repayments_amt : 0,
            close_loan_lst: [],
            open_close_loan_lst: [],
            total_interest_rate : 0,
            total_interest_lst : [],
            all_loan_lst : [],
            paid_repayment_lst : [],
            all_aprv_loan_lst : [],
            all_disburse_lst : [],
            all_loan_lead : [],
            invoice_process_fees : 0,
            invoice_lst : [],
            open_loan_lst : [],
            company_currency: 'USD',
            all_upcoming_installment_list :{},
            all_upcoming_ins_list_length : 0,
            rowsPerPage : 10,
            currentUpcInsLst_page : 1,
            all_overdue_installment_list :{},
            all_overdue_ins_list_length : 0,
            rowsPerPage : 10,
            currentOverInsLst_page : 1,
            total_principle_amt :0,
            total_interest_amt :0,
            total_int_n_pri_amt : 0,
            user_name : {},
            user_img : {}
        });
        onWillStart(this.onWillStart);
        onMounted(this.onMounted);
    }

    async onWillStart() {        
        await this.getLoanData()
        await this.getGreetings()
        await loadJS("https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js")
        await loadJS("https://cdnjs.cloudflare.com/ajax/libs/hammer.js/2.0.8/hammer.min.js")
        await loadJS("https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-zoom/2.0.1/chartjs-plugin-zoom.min.js")
    }

    _downloadChart(e) {
        var chartId = e.target.id.slice(0, e.target.id.length - 4)
        var chartEle = document.querySelector("#" + chartId)
        const imageDataURL = chartEle.toDataURL('image/png'); // Generate image data URL
        const filename = chartId + '.png'; // Set your preferred filename
        const link = document.createElement('a');
        link.href = imageDataURL;
        link.download = filename;
        link.click();
    }

    async getGreetings() {
        var self = this;
        const now = new Date();
        const hours = now.getHours();
        if (hours >= 5 && hours < 12) {
            self.greetings = "Good Morning";
        }
        else if (hours >= 12 && hours < 18) {
            self.greetings = "Good Afternoon";
        }
        else {
            self.greetings = "Good Evening";
        }
    }

    async onMounted() {
        this._onchangeMonthLoanReqChart();
        this.loan_collection_state_chart_data();
        this.loan_emi_amount_chart_data();
        this.partner_loan_amount_chart_data();
        this.loan_installment_chart_data();
        this._onchangeLoanTypeChart();
        this.loan_state_wise_chart_data();
        this.render_upcoming_installment_list(this.state.rowsPerPage, this.state.currentUpcInsLst_page);
        this.render_overdue_installment_list(this.state.rowsPerPage, this.state.currentOverInsLst_page);
        this.render_loan_filter();
    }

    downloadReport(e) {
        window.print()
//        e.stopPropagation();
//        e.preventDefault();
//
//        var opt = {
//            margin: 1,
//            filename: 'LoanDashboard.pdf',
//            image: { type: 'jpeg', quality: 0.98 },
//            html2canvas: { scale: 2 },
//            jsPDF: { unit: 'px', format: [1920, 1080], orientation: 'landscape' }
//        };
//        html2pdf().set(opt).from(document.getElementById("dashboard")).save()
    }

    render_loan_filter() {
        rpc('/loan/filter').then(function (data) {
            var users = data[0]
            var borrowers = data[1]
            var loan_type = data[2]

//            $(users).each(function (user) {
//                $('#user_selection').append("<option value=" + users[user].id + ">" + users[user].name + "</option>");
//            });
//            $(borrowers).each(function (borrower) {
//                $('#borrowers_selection').append("<option value=" + borrowers[borrower].id + ">" + borrowers[borrower].name + "</option>");
//            });
//            $(loan_type).each(function (type) {
//                $('#loan_type_selection').append("<option value=" + loan_type[type].id + ">" + loan_type[type].name + "</option>");
//            });

			users.forEach(user => {
				const option = document.createElement('option');
				option.value = user.id;
				option.textContent = user.name;
				document.querySelector('#user_selection').appendChild(option);
			});

             borrowers.forEach(borrower => {
				const option = document.createElement('option');
				option.value = borrower.id;
				option.textContent = borrower.name;
				document.querySelector('#borrowers_selection').appendChild(option);
			});

			loan_type.forEach(loan_type => {
				const option = document.createElement('option');
				option.value = loan_type.id;
				option.textContent = loan_type.name;
				document.querySelector('#loan_type_selection').appendChild(option);
			});
        });
    }

    async getLoanData() {
        var self = this;
//        jsonrpc('/get/loan/tiles/data').then(function (data) {
        const data = await rpc('/get/loan/tiles/data');
        self.state.company_currency = data['company_currency']
        self.state.total_aprv_amt = data['total_aprv_amt'].toLocaleString('en-US', { style: 'currency', currency: self.state.company_currency })
        self.state.total_disburse_amt = data['total_disburse_amt'].toLocaleString('en-US', { style: 'currency', currency: self.state.company_currency })
        self.state.repayments_amt = data['repayments_amt'].toLocaleString('en-US', { style: 'currency', currency: self.state.company_currency })
        self.state.close_loan_lst = data['close_loan_lst']
        self.state.open_close_loan_lst = data['open_close_loan_lst']
        self.state.total_interest_rate =data['total_interest_rate']
        self.state.total_interest_lst = data['total_interest_lst'].toLocaleString('en-US', { style: 'currency', currency: self.state.company_currency })
        self.state.all_loan_lst = data['all_loan_lst']
        self.state.paid_repayment_lst = data['paid_repayment_lst']
        self.state.all_aprv_loan_lst = data['all_aprv_loan_lst']
        self.state.all_disburse_lst = data['all_disburse_lst']
        self.state.all_loan_lead = data['all_loan_lead']
        self.state.invoice_process_fees = data['invoice_process_fees'].toLocaleString('en-US', { style: 'currency', currency: self.state.company_currency })
        self.state.invoice_lst = data['invoice_lst'],
        self.state.open_loan_lst = data['open_loan_lst']
        self.state.user_name = data['user_name'],
        self.state.user_img = data['user_img']
//        });
        return data;
    }

//    show_date_range_block() {
//        document.querySelector('#date-block').show();
//    }
show_date_range_block() {
    document.querySelector('#date-block').style.display = 'block'; // or ''
}

    _onchangeLoanFilter(ev) {
        this.flag = 1
        var user_selection = document.querySelector('#user_selection').value;
        var borrowers_selection = document.querySelector('#borrowers_selection').value;
        var loan_type_selection =  document.querySelector('#loan_type_selection').value;
        var duration_selection = document.querySelector('#loan_duration_selection').value;
        var start_date = document.querySelector('#start_date').value;
        var end_date = document.querySelector('#end_date').value;
        if (duration_selection == 'custom_range') {
            this.show_date_range_block()
        } else {
//            document.querySelector('#date-block').hide();
                document.querySelector('#date-block').style.display = 'none';
        }

        var self = this;
        rpc('/loan/filter-apply', {
            'data': {
                'user': user_selection,
                'borrower': borrowers_selection,
                'type':loan_type_selection,
                'duration':duration_selection,
                'start_date': start_date,
                'end_date': end_date,
            }
        }).then(function (data) {
        self.state.total_aprv_amt = data['total_aprv_amt'].toLocaleString('en-US', { style: 'currency', currency: self.state.company_currency })
        self.state.total_disburse_amt = data['total_disburse_amt'].toLocaleString('en-US', { style: 'currency', currency: self.state.company_currency })
        self.state.repayments_amt = data['repayments_amt'].toLocaleString('en-US', { style: 'currency', currency: self.state.company_currency })
        self.state.close_loan_lst = data['close_loan_lst']
        self.state.open_close_loan_lst = data['open_close_loan_lst']
        self.state.total_interest_rate =data['total_interest_rate']
        self.state.total_interest_lst = data['total_interest_lst'].toLocaleString('en-US', { style: 'currency', currency: self.state.company_currency })
        self.state.all_loan_lst = data['all_loan_lst']
        self.state.paid_repayment_lst = data['paid_repayment_lst']
        self.state.all_aprv_loan_lst = data['all_aprv_loan_lst']
        self.state.all_disburse_lst = data['all_disburse_lst']
        self.state.all_loan_lead = data['all_loan_lead']
        self.state.invoice_process_fees = data['invoice_process_fees'].toLocaleString('en-US', { style: 'currency', currency: self.state.company_currency })
        self.state.invoice_lst = data['invoice_lst'],
        self.state.open_loan_lst = data['open_loan_lst']
        })
        this._onchangeMonthLoanReqChart()
        this.loan_collection_state_chart_data()
        this.loan_emi_amount_chart_data()
        this.partner_loan_amount_chart_data()
        this.loan_installment_chart_data()
        this._onchangeLoanTypeChart()
        this.loan_state_wise_chart_data()
        this.render_upcoming_installment_list(this.state.rowsPerPage, this.state.currentUpcInsLst_page);
        this.render_overdue_installment_list(this.state.rowsPerPage, this.state.currentOverInsLst_page);

    }

    async _onchangeMonthLoanReqChart(ev){
        var user_selection = document.querySelector('#user_selection').value;
        var borrowers_selection = document.querySelector('#borrowers_selection').value;
        var loan_type_selection =  document.querySelector('#loan_type_selection').value;
        var duration_selection = document.querySelector('#loan_duration_selection').value;
        var start_date = document.querySelector('#start_date').value;
        var end_date = document.querySelector('#end_date').value;
        var self = this;
        await rpc("/month/loan/request/chart/data",
        {
        'data':
            {
                'user': user_selection,
                'borrower': borrowers_selection,
                'type': loan_type_selection,
                'duration':duration_selection,
                'start_date': start_date,
                'end_date': end_date,
            }
        }).then(function (data)
        {
            var ctx = document.querySelector("#loan_req_chart_data");
            new Chart(ctx, {
                type: 'bar',
                data: data.loan_request_chart_data,
                options: {
                    barThickness : 20,
                    indexAxis: 'y',

                    maintainAspectRatio: false,

                    onClick: (evt, elements) => {
                        if (elements.length > 0) {
                            const element = elements[0];
                            const clickedIndex = element.index;
                            const clickedLabel = data.loan_request_chart_data.labels[clickedIndex];
                            const clickedValue = data.loan_request_chart_data.datasets[0].detail[clickedIndex]
                            var options = {
                            };
                            self.action.doAction({
                                name: _t(clickedLabel),
                                type: 'ir.actions.act_window',
                                res_model: 'dev.loan.loan',
                                domain: [["id", "in", clickedValue]],
                                view_mode: 'list,form',
                                views: [
                                    [false, 'list'],
                                    [false, 'form']
                                ],
                                target: 'current'
                            }, options)
                        } else {
                        }
                    }
                }
            });
        });
    }

    async loan_collection_state_chart_data(ev) {
        var user_selection = document.querySelector('#user_selection').value;
        var borrowers_selection = document.querySelector('#borrowers_selection').value;
        var loan_type_selection =  document.querySelector('#loan_type_selection').value;
        var duration_selection = document.querySelector('#loan_duration_selection').value;
        var start_date = document.querySelector('#start_date').value;
        var end_date = document.querySelector('#end_date').value;

        var self = this;
        await rpc("/collection/state/chart/data", {
        'data':
            {
                'user': user_selection,
                'borrower': borrowers_selection,
                'type': loan_type_selection,
                'duration':duration_selection,
                'start_date': start_date,
                'end_date': end_date,
            }
        }).then(function (data) {
            var ctx = document.querySelector("#collection_state_chart_data");
            new Chart(ctx, {
                type: 'doughnut',
                data: data.loan_installment_chart_data,
                options: {
                    maintainAspectRatio: false,

                    onClick: (evt, elements) => {
                        if (elements.length > 0) {
                            const element = elements[0];
                            const clickedIndex = element.index;
                            const clickedLabel = data.loan_installment_chart_data.labels[clickedIndex];
                            const clickedValue = data.loan_installment_chart_data.datasets[0].detail[clickedIndex]
                            var options = {
                            };
                            self.action.doAction({
                                name: _t(clickedLabel),
                                type: 'ir.actions.act_window',
                                res_model: 'dev.loan.installment',
                                domain: [["id", "in", clickedValue]],
                                view_mode: 'list,form',
                                views: [
                                    [false, 'list'],
                                    [false, 'form']
                                ],
                                target: 'current'
                            }, options)
                        } else {
                        }
                    }
                }
            });
        });
    }

    async loan_emi_amount_chart_data(ev) {
        var user_selection = document.querySelector('#user_selection').value;
        var borrowers_selection = document.querySelector('#borrowers_selection').value;
        var loan_type_selection =  document.querySelector('#loan_type_selection').value;
        var duration_selection = document.querySelector('#loan_duration_selection').value;
        var start_date = document.querySelector('#start_date').value;
        var end_date = document.querySelector('#end_date').value;

        var self = this;
        await rpc("/emi/amount/chart/data", {
        'data':
            {
                'user': user_selection,
                'borrower': borrowers_selection,
                'type': loan_type_selection,
                'duration':duration_selection,
                'start_date': start_date,
                'end_date': end_date,
            }
        }).then(function (data) {
            var int = document.getElementById("intetestAmt");
            var pri = document.getElementById("principaltAmt");

            var result = data.loan_emi_amount_chart_data
            var p_amt=parseFloat(result.principle_amount)
            var i_amt =parseFloat(result.interest_amount)
            self.state.total_principle_amt = p_amt.toLocaleString('en-US', { style: 'currency', currency: self.state.company_currency})
            self.state.total_interest_amt = i_amt.toLocaleString('en-US', { style: 'currency', currency: self.state.company_currency})
            self.state.total_int_n_pri_amt = (p_amt+ i_amt).toLocaleString('en-US', { style: 'currency', currency: self.state.company_currency})
            int.style.width = (result.interest_amount / (result.interest_amount + result.principle_amount)) * 100 + "%"
            pri.style.width = (result.principle_amount / (result.interest_amount + result.principle_amount)) * 100 + "%"
        });
    }

    async partner_loan_amount_chart_data(ev) {
        var user_selection = document.querySelector('#user_selection').value;
        var borrowers_selection = document.querySelector('#borrowers_selection').value;
        var loan_type_selection =  document.querySelector('#loan_type_selection').value;
        var duration_selection = document.querySelector('#loan_duration_selection').value;
        var start_date = document.querySelector('#start_date').value;
        var end_date = document.querySelector('#end_date').value;
        var top_partner_loan_count = document.querySelector('#top_partner_loan_count').value;

        var self = this;
        await rpc("/top/loan/amount/partner/chart/data",
            {
                'data':
                {
                    'top_partner_loan_count': top_partner_loan_count,
                    'user': user_selection,
                    'borrower': borrowers_selection,
                    'type': loan_type_selection,
                    'duration':duration_selection,
                    'start_date': start_date,
                    'end_date': end_date,
                }
            }).then(function (data) {
                var ctx = document.querySelector("#partner_loan_amount_chart_data");
                new Chart(ctx, {
                    type: 'pie',
                    data: data.partner_loan_chart_data,
                    options: {
                        maintainAspectRatio: false,

                        onClick: (evt, elements) => {
                            if (elements.length > 0) {
                                const element = elements[0];
                                const clickedIndex = element.index;
                                const clickedLabel = data.partner_loan_chart_data.labels[clickedIndex];
                                const clickedValue = data.partner_loan_chart_data.datasets[0].detail[clickedIndex]
                                var options = {
                                };
                                self.action.doAction({
                                    name: _t(clickedLabel),
                                    type: 'ir.actions.act_window',
                                    res_model: 'dev.loan.loan',
                                    domain: [["id", "in", clickedValue]],
                                    view_mode: 'list,form',
                                    views: [
                                        [false, 'list'],
                                        [false, 'form']
                                    ],
                                    target: 'current'
                                }, options)
                            } else {
                            }
                        }
                    }
                });
            });
    }

    async loan_installment_chart_data(){
        var top_partner_installment_count = document.querySelector('#top_partner_installment_count').value;
        var user_selection = document.querySelector('#user_selection').value;
        var borrowers_selection = document.querySelector('#borrowers_selection').value;
        var loan_type_selection =  document.querySelector('#loan_type_selection').value;
        var duration_selection =document.querySelector('#loan_duration_selection').value;
        var start_date = document.querySelector('#start_date').value;
        var end_date = document.querySelector('#end_date').value;

		var self = this;
		await rpc("/loan/installment/chart/data", {
            'data': {
                    'top_partner_installment_count': top_partner_installment_count,
                    'user': user_selection,
                    'borrower': borrowers_selection,
                    'type': loan_type_selection,
                    'duration':duration_selection,
                    'start_date': start_date,
                    'end_date': end_date,
            }
		}).then(function(data){
			 var ctx = document.querySelector("#loan_installment");
             new Chart(ctx, {
			 	type: "bar",
			 	data: data.loan_installment_chart_data,
			 	options: {
                     maintainAspectRatio: false,
                     barThickness : 20,
                     responsive : true,
                     scales: {
                         x:{
                                stacked : true,
                         },
                          y: {
                            ticks: {
                                beginAtZero: true,
                                stepSize: 3
                            }
                        }
                    },
                }
			 });
        });

    }

    async _onchangeLoanTypeChart(ev) {
        var user_selection = document.querySelector('#user_selection').value;
        var borrowers_selection = document.querySelector('#borrowers_selection').value;
        var loan_type_selection =  document.querySelector('#loan_type_selection').value;
        var duration_selection = document.querySelector('#loan_duration_selection').value;
        var start_date = document.querySelector('#start_date').value;
        var end_date = document.querySelector('#end_date').value;
        var self = this;
        await rpc("/loan/type/chart/data",
        {
        'data':
            {
                    'user': user_selection,
                    'borrower': borrowers_selection,
                    'type': loan_type_selection,
                    'duration':duration_selection,
                    'start_date': start_date,
                    'end_date': end_date,
            }
        }).then(function (data)
        {
            var ctx = document.querySelector("#loan_type_chart_data");
            new Chart(ctx, {
                type: 'pie',
                data: data.loan_type_chart_data,
                options: {
                    maintainAspectRatio: false,

                    onClick: (evt, elements) => {
                        if (elements.length > 0) {
                            const element = elements[0];
                            const clickedIndex = element.index;
                            const clickedLabel = data.loan_type_chart_data.labels[clickedIndex];
                            const clickedValue = data.loan_type_chart_data.datasets[0].detail[clickedIndex]
                            var options = {
                            };
                            self.action.doAction({
                                name: _t(clickedLabel),
                                type: 'ir.actions.act_window',
                                res_model: 'dev.loan.loan',
                                domain: [["id", "in", clickedValue]],
                                view_mode: 'list,form',
                                views: [
                                    [false, 'list'],
                                    [false, 'form']
                                ],
                                target: 'current'
                            }, options)
                        } else {
                        }
                    }
                }
            });
        });
    }

//    Loan state wise chart
    async loan_state_wise_chart_data(ev) {
        var user_selection = document.querySelector('#user_selection').value;
        var borrowers_selection = document.querySelector('#borrowers_selection').value;
        var loan_type_selection =  document.querySelector('#loan_type_selection').value;
        var duration_selection = document.querySelector('#loan_duration_selection').value;
        var start_date = document.querySelector('#start_date').value;
        var end_date = document.querySelector('#end_date').value;

        var self = this;
        await rpc("/loan/state/wise/chart/data", {
        'data':
            {
                'user': user_selection,
                'borrower': borrowers_selection,
                'type': loan_type_selection,
                'duration':duration_selection,
                'start_date': start_date,
                'end_date': end_date,
            }
        }).then(function (data) {
            var ctx = document.querySelector("#loan_state_chart_data");
            new Chart(ctx, {
                type: 'bar',
                data: data.loan_state_wise_chart_data,
                options: {
                    maintainAspectRatio: false,

                    onClick: (evt, elements) => {
                        if (elements.length > 0) {
                            const element = elements[0];
                            const clickedIndex = element.index;
                            const clickedLabel = data.loan_state_wise_chart_data.labels[clickedIndex];
                            const clickedValue = data.loan_state_wise_chart_data.datasets[0].detail[clickedIndex]
                            var options = {
                            };
                            self.action.doAction({
                                name: _t(clickedLabel),
                                type: 'ir.actions.act_window',
                                res_model: 'dev.loan.loan',
                                domain: [["id", "in", clickedValue]],
                                view_mode: 'list,form',
                                views: [
                                    [false, 'list'],
                                    [false, 'form']
                                ],
                                target: 'current'
                            }, options)
                        } else {
                        }
                    }
                }
            });
        });
    }


//       upcoming installment List
    async render_upcoming_installment_list(rowsPerPage, page) {
        var user_selection = document.querySelector('#user_selection').value;
        var borrowers_selection = document.querySelector('#borrowers_selection').value;
        var loan_type_selection =  document.querySelector('#loan_type_selection').value;
        var loan_upcoming_selection = document.querySelector('#loan_upcoming_selection').value;
//        var duration_selection = $('#loan_duration_selection').val();
//        var start_date = $('#start_date').val();
//        var end_date = $('#end_date').val();
        self = this
        await rpc("/upcoming/installment/list/data", {
        'data':
            {
                    'user': user_selection,
                    'borrower': borrowers_selection,
                    'type': loan_type_selection,
                    'upc_duration':loan_upcoming_selection
//                    'duration':duration_selection,
//                    'start_date': start_date,
//                    'end_date': end_date,
            }
        }).then(function (data) {
            self.state.all_upcoming_installment_list = data['all_upcoming_installment'];
            var tbody = document.querySelector("#all_upcoming_installment_list tbody");
            tbody.innerHTML = '';

            self.state.all_upcoming_ins_list_length = self.state.all_upcoming_installment_list.length

            const start = (page - 1) * rowsPerPage;
            const end = start + rowsPerPage;
            const paginatedData =  self.state.all_upcoming_installment_list.slice(start, end)
            console.log("paginatedData",paginatedData);

            for (var i = 0; i < paginatedData.length; i++) {
                var row = document.createElement("tr");
                for (var key in paginatedData[i]) {
                    if (key !== 'id') {
                        var cell = document.createElement("td");
                        if (paginatedData[i][key].length == 2) {
                            cell.textContent = paginatedData[i][key][1];
                            row.appendChild(cell);
                        }
                        else if (key === 'date') {
                            var cell = document.createElement("td");
                            var date = paginatedData[i]['date']
                            if (date) {
                                var date_splited = date.split(' ')[0].split('-');
                                cell.textContent = date_splited[2] + '-' + date_splited[1] + '-' + date_splited[0];
                            }
                            else {
                                cell.textContent = '-'
                            }
                            row.appendChild(cell);
                        }
                        else if (key ==='amount'){
                        var amount =  paginatedData[i]['amount']
                        if(amount)
                        {
                        var cell = document.createElement("td");
                        cell.textContent = parseFloat(paginatedData[i][key]).toFixed(2)
                        }
                        else
                        {
                        cell.textContent = paginatedData[i][key];
                        }
                         row.appendChild(cell);
                        }

                        else {
                            if (paginatedData[i][key] == false) {
                                cell.textContent = '-';
                                row.appendChild(cell);
                            }
                            else {
                                cell.textContent = paginatedData[i][key];
                                row.appendChild(cell);
                            }
                        }

                    }
                }
                var buttonCell = document.createElement("td");
                var button = document.createElement("button");
                button.textContent = "View";
                button.className = "btn-primary rounded p-2";
                button.style.border = "none";

                button.setAttribute("data-id", paginatedData[i].id);
                button.addEventListener("click", function () {
                    var id = this.getAttribute("data-id");
                    // Call your function with the ID
                    installment_tree_button_function(id);
                });
                buttonCell.appendChild(button);
                row.appendChild(buttonCell);
                tbody.appendChild(row);
            }

            function installment_tree_button_function(id) {
                var options = {
                };
                self.action.doAction({
                    name: _t("Installment"),
                    type: 'ir.actions.act_window',
                    res_model: 'dev.loan.installment',
                    domain: [["id", "=", id]],
                    view_mode: 'list,form',
                    views: [
                        [false, 'list'],
                        [false, 'form']
                    ],
                    target: 'current'
                }, options)

            }
        });
    }

     upcomingPrevPage(e) {
        if (this.state.currentUpcInsLst_page > 1) {
            this.state.currentUpcInsLst_page--;
            this.render_upcoming_installment_list(this.state.rowsPerPage, this.state.currentUpcInsLst_page);
            document.getElementById("upcoming_next_button").disabled = false;
        }
        if (this.state.currentUpcInsLst_page == 1) {
            document.getElementById("upcoming_prev_button").disabled = true;
        } else {
            document.getElementById("upcoming_prev_button").disabled = false;
        }
    }

     upcomingNextPage() {
        if ((this.state.currentUpcInsLst_page * this.state.rowsPerPage) < this.state.all_upcoming_ins_list_length) {
            this.state.currentUpcInsLst_page++;
            this.render_upcoming_installment_list(this.state.rowsPerPage, this.state.currentUpcInsLst_page);
            document.getElementById("upcoming_prev_button").disabled = false;
        }
        if (Math.ceil(this.state.all_upcoming_ins_list_length / this.state.rowsPerPage) == this.state.all_upcoming_ins_list_length) {
            document.getElementById("upcoming_next_button").disabled = true;
        } else {
            document.getElementById("upcoming_next_button").disabled = false;
        }
    }
//overdue installment list
    async render_overdue_installment_list(rowsPerPage, page) {
        var user_selection = document.querySelector('#user_selection').value;
        var borrowers_selection = document.querySelector('#borrowers_selection').value;
        var loan_type_selection =  document.querySelector('#loan_type_selection').value;
        var duration_selection = document.querySelector('#loan_duration_selection').value;
        var start_date = document.querySelector('#start_date').value;
        var end_date = document.querySelector('#end_date').value;
        self = this
        await rpc("/overdue/installment/list/data", {
        'data':
            {
                    'user': user_selection,
                    'borrower': borrowers_selection,
                    'type': loan_type_selection,
                    'duration':duration_selection,
                    'start_date': start_date,
                    'end_date': end_date,
            }
        }).then(function (data) {
            self.state.all_overdue_installment_list = data['all_overdue_installment'];
            var tbody = document.querySelector("#all_overdue_installment_list tbody");
            tbody.innerHTML = '';

            self.state.all_overdue_ins_list_length = self.state.all_overdue_installment_list.length

            const start = (page - 1) * rowsPerPage;
            const end = start + rowsPerPage;
            const paginatedData =  self.state.all_overdue_installment_list.slice(start, end)
            console.log("paginatedData",paginatedData);

            for (var i = 0; i < paginatedData.length; i++) {
                var row = document.createElement("tr");
                for (var key in paginatedData[i]) {
                    if (key !== 'id') {
                        var cell = document.createElement("td");
                        if (paginatedData[i][key].length == 2) {
                            cell.textContent = paginatedData[i][key][1];
                            row.appendChild(cell);
                        }
                        else if (key === 'date') {
                            var cell = document.createElement("td");
                            var date = paginatedData[i]['date']
                            if (date) {
                                var date_splited = date.split(' ')[0].split('-');
                                cell.textContent = date_splited[2] + '-' + date_splited[1] + '-' + date_splited[0];
                            }
                            else {
                                cell.textContent = '-'
                            }
                            row.appendChild(cell);
                        }
                        else if (key ==='amount'){
                        var amount =  paginatedData[i]['amount']
                        if(amount)
                        {
                        var cell = document.createElement("td");
                        cell.textContent = parseFloat(paginatedData[i][key]).toFixed(2)
                        }
                        else
                        {
                        cell.textContent = paginatedData[i][key];
                        }
                         row.appendChild(cell);
                        }


                        else {
                            if (paginatedData[i][key] == false) {
                                cell.textContent = '-';
                                row.appendChild(cell);
                            }
                            else {
                                cell.textContent = paginatedData[i][key];
                                row.appendChild(cell);
                            }
                        }

                    }
                }
                var buttonCell = document.createElement("td");
                var button = document.createElement("button");
                button.textContent = "View";
                button.className = "btn-primary rounded p-2";
                button.style.border = "none";

                button.setAttribute("data-id", paginatedData[i].id);
                button.addEventListener("click", function () {
                    var id = this.getAttribute("data-id");
                    // Call your function with the ID
                    overdue_tree_button_function(id);
                });
                buttonCell.appendChild(button);
                row.appendChild(buttonCell);
                tbody.appendChild(row);
            }

            function overdue_tree_button_function(id) {
                var options = {
                };
                self.action.doAction({
                    name: _t("Installment"),
                    type: 'ir.actions.act_window',
                    res_model: 'dev.loan.installment',
                    domain: [["id", "=", id]],
                    view_mode: 'list,form',
                    views: [
                        [false, 'list'],
                        [false, 'form']
                    ],
                    target: 'current'
                }, options)

            }
        });
    }

    overduePrevPage(e) {
        if (this.state.currentOverInsLst_page > 1) {
            this.state.currentOverInsLst_page--;
            this.render_overdue_installment_list(this.state.rowsPerPage, this.state.currentOverInsLst_page);
            document.getElementById("overdue_next_button").disabled = false;
        }
        if (this.state.currentOverInsLst_page == 1) {
            document.getElementById("overdue_prev_button").disabled = true;
        } else {
            document.getElementById("overdue_prev_button").disabled = false;
        }
    }

    overdueNextPage() {
        if ((this.state.currentOverInsLst_page * this.state.rowsPerPage) < this.state.all_overdue_ins_list_length) {
            this.state.currentOverInsLst_page++;
            this.render_overdue_installment_list(this.state.rowsPerPage, this.state.currentOverInsLst_page);
            document.getElementById("overdue_prev_button").disabled = false;
        }
        if (Math.ceil(this.state.all_overdue_ins_list_length / this.state.rowsPerPage) == this.state.all_overdue_ins_list_length) {
            document.getElementById("overdue_next_button").disabled = true;
        } else {
            document.getElementById("overdue_next_button").disabled = false;
        }
    }


    action_loan_lead(e) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        var domain = [["id", "=", this.state.all_loan_lead]]
        this.action.doAction({
            name: _t("Loan Lead"),
            type: 'ir.actions.act_window',
            res_model: 'crm.lead',
            domain: domain,
            view_mode: 'list,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options)
    }
    action_disburse_loan_lst(e) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        var domain = [["id", "=", this.state.all_disburse_lst]]
        this.action.doAction({
            name: _t("Disburse Loan"),
            type: 'ir.actions.act_window',
            res_model: 'dev.loan.loan',
            domain: domain,
            view_mode: 'list,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options)
    }

    action_invoice_lst(e) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        var domain = [["id", "=", this.state.invoice_lst]]
        this.action.doAction({
            name: _t("Invoice"),
            type: 'ir.actions.act_window',
            res_model: 'account.move',
            domain: domain,
            view_mode: 'list,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options)
    }

    action_approve_loan_lst(e) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        var domain = [["id", "=", this.state.all_aprv_loan_lst]]
        this.action.doAction({
            name: _t("Approve Loan"),
            type: 'ir.actions.act_window',
            res_model: 'dev.loan.loan',
            domain: domain,
            view_mode: 'list,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options)
    }

    action_all_lst(e) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        var domain = [["id", "=", this.state.open_loan_lst]]
        this.action.doAction({
            name: _t("All Loan"),
            type: 'ir.actions.act_window',
            res_model: 'dev.loan.loan',
            domain: domain,
            view_mode: 'list,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options)
    }

    action_close_loan(e) {
        e.stopPropagation();
        e.preventDefault();
        var cont = {search_default_no_share: true};
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        var domain = [["id", "=", this.state.open_close_loan_lst]]
        cont = {
                    search_default_no_share: true,
                    search_default_state:true,
                }
        this.action.doAction({
            name: _t("Close Loan"),
            type: 'ir.actions.act_window',
            res_model: 'dev.loan.loan',
            context: cont,
            domain: domain,
            view_mode: 'list,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options)
    }

    action_loan_repayments(e) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        var domain = [["id", "=", this.state.paid_repayment_lst]]
        this.action.doAction({
            name: _t("Repayments"),
            type: 'ir.actions.act_window',
            res_model: 'dev.loan.installment',
            domain: domain,
            view_mode: 'list,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options)
    }

}

LoanDashboard.template = "LoanDashboard"
registry.category("actions").add("open_loan_dashboard", LoanDashboard)