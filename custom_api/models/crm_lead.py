from odoo import models, fields, api, _

class Opportunity(models.Model):
    _inherit = "crm.lead"
    _description = 'Additional Opportunity Info'

    partner_latitude = fields.Float(string='Geo Latitude', digits=(10, 7))
    partner_longitude = fields.Float(string='Geo Longitude', digits=(10, 7))
    building_stage = fields.Char(string='Building Stage')

    opp_erp_id = fields.Char(string='ERP ID', store=True, readonly=True, copy=False, default='New')

    # NEW – show partner's lead image on the opportunity form
    partner_lead_image = fields.Image(
        string="Partner Picture",
        related="partner_id.lead_image",   # points to the field you added on res.partner
        readonly=True,
        store=False,                       # no duplicate copy in the database
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Assign unique ERP IDs to leads and opportunities using their respective sequences."""
        for vals in vals_list:
            record_type = vals.get("type", "opportunity")
            if record_type == "lead":
                if vals.get("opp_erp_id", "New") == "New":
                    vals["opp_erp_id"] = self.env["ir.sequence"].next_by_code("opp.erp.id.sequence") or "/"
        return super().create(vals_list)


class LeadInfo(models.Model):
    _inherit = "res.partner"
    _description = 'Additional Customer/Lead Info'

    lead_status = fields.Selection([
        ('qualified', 'Qualified'),
        ('unqualified', 'Unqualified'),
    ], string='Status', default='unqualified')
    lead_erp_id = fields.Char(
        string='ERP ID',
        store=True,
        readonly=True,
        copy=False,
        default='New')
    lead_image = fields.Image(string="Image", max_width=1920, max_height=1920)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("lead_erp_id", "New") == "New":
                vals["lead_erp_id"] = self.env["ir.sequence"].next_by_code("erp.id.sequence") or "/"
        return super().create(vals_list)
