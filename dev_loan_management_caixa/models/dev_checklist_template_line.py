from odoo import models, fields, api, _

# class ChecklistTemplate(models.Model):
#     _name = 'dev.checklist.template'
#     _description = 'Checklist Template'
#
#     loan_type_id = fields.Many2one('dev.loan.type', string="Loan Type", required=True)
#     line_ids = fields.One2many('dev.checklist.template.line', 'type_id', string="Checklist Lines")


class ChecklistTemplateLine(models.Model):
    _name = "dev.checklist.template.line"
    _description = "Checklist Template Line"

    name = fields.Char(required=True)
    type_id = fields.Many2one("dev.loan.type", string="Loan Type", required=True)

