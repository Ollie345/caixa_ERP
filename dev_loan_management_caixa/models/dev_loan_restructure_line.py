# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class DevLoanRestructureLine(models.Model):
    _name = 'dev.loan.restructure.line'
    _description = 'Loan Restructure Schedule Line'
    _order = 'date'

    restructure_id = fields.Many2one('dev.loan.restructure', string='Restructure', required=True, ondelete='cascade')
    date = fields.Date(string='Due Date', required=True)
    principal = fields.Monetary(string='Principal', currency_field='currency_id', required=True)
    interest = fields.Monetary(string='Interest', currency_field='currency_id', required=True)
    total = fields.Monetary(string='Total', currency_field='currency_id', compute='_compute_total', store=True)
    remaining_balance = fields.Monetary(string='Remaining Balance', currency_field='currency_id')

    currency_id = fields.Many2one(related='restructure_id.currency_id', store=True)
    company_id = fields.Many2one(related='restructure_id.company_id', store=True)

    @api.depends('principal', 'interest')
    def _compute_total(self):
        for line in self:
            line.total = (line.principal or 0.0) + (line.interest or 0.0)


