# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed ine the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """Extend partner model with wallet information"""
    _inherit = 'res.partner'
    
    # Wallet Information
    wallet_account_number = fields.Char(
        string='Wallet Account Number',
        copy=False,
        help='BaaS wallet account number assigned to this partner'
    )
    wallet_tier = fields.Selection(
        selection=[
            ('tier_1', 'Tier 1'),
            ('tier_2', 'Tier 2'),
            ('tier_3', 'Tier 3'),
        ],
        string='Wallet Tier',
        default='tier_2',
        copy=False,
        help='Wallet tier level (Tier 1, 2, or 3)'
    )
    wallet_status = fields.Selection(
        selection=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('frozen', 'Frozen'),
            ('closed', 'Closed'),
        ],
        string='Wallet Status',
        default='active',
        copy=False,
        help='Current status of the wallet'
    )
    wallet_created_date = fields.Datetime(
        string='Wallet Created Date',
        copy=False,
        help='Date and time when the wallet was created'
    )
    baas_wallet_id = fields.Char(
        string='BaaS Wallet ID',
        copy=False,
        help='Additional BaaS wallet identifier if provided'
    )
    # wallet_creation_reference = fields.Char(
    #     string='Account Creation Reference',
    #     copy=False,
    #     help='Submission reference for asynchronous Tier 3 wallet creation'
    # )
    # wallet_creation_status = fields.Selection(
    #     selection=[
    #         ('PENDING', 'Pending'),
    #         ('COMPLETED', 'Completed'),
    #         ('FAILED', 'Failed'),
    #         ('REJECTED', 'Rejected'),
    #     ],
    #     string='Creation Status',
    #     copy=False,
    #     help='Status of the asynchronous wallet creation request'
    # )
    wallet_balance = fields.Monetary(
        string='Wallet Balance',
        compute='_compute_wallet_balance',
        currency_field='wallet_currency_id',
        help='Current wallet balance (fetched from BaaS API)',
        store=False
    )
    wallet_currency_id = fields.Many2one(
        'res.currency',
        string='Wallet Currency',
        default=lambda self: self.env.ref('base.NGN', raise_if_not_found=False) or self.env.company.currency_id,
        help='Currency for wallet balance'
    )
    wallet_balance_last_updated = fields.Datetime(
        string='Balance Last Updated',
        help='Last time wallet balance was fetched'
    )
    
    # Tier 3 KYC Fields
    # lga = fields.Char(
    #     string='LGA',
    #     help='Local Government Area (required for Tier 3)'
    # )
    # utility_bill = fields.Binary(
    #     string='Utility Bill',
    #     attachment=True,
    #     help='Utility bill image for Tier 3 KYC verification'
    # )
    # utility_bill_name = fields.Char(
    #     string='Utility Bill Filename'
    # )

    def create_wallet_tier_two(self, bvn=None, phone=None):
        """Create Tier Two wallet for this partner
        
        This method is a copy of the former tier‑one implementation; the
        only differences are the endpoint that is called and the value written
        to ``wallet_tier``.  The old tier‑one name is kept below as a
        thin wrapper for backwards compatibility.
        :param bvn: Bank Verification Number (optional, falls back to partner field)
        :param phone: Phone number (optional, falls back to partner field)
        :return: dict with creation result
        """
        self.ensure_one()
        # ------------------------------------------------------------------
        # TEST ENVIRONMENT: skip the normal payload construction and external
        # call, use a fixed set of values instead.  Remove/comment-out this
        # block when switching back to the real BAAS endpoint.
        hardcoded_data = {
            "bvn": "00003400011",
            "dob": "1990-01-15",
            "firstname": "Joe",
            "lastname": "Doe",
            "nin": "00004300222",
            "phone": "1231111292",
        }
        _logger.info("creating tier‑2 wallet with hardcoded test data: %s", hardcoded_data)
        test_account = "TESTWALLET0001"
        self.write({
            'wallet_account_number': test_account,
            'wallet_tier': 'tier_2',
            'wallet_status': 'active',
            'wallet_created_date': fields.Datetime.now(),
        })
        return {
            'success': True,
            'account_number': test_account,
            'message': 'Hardcoded wallet created (test)',
        }
        # ------------------------------------------------------------------
        # original logic below left in comments for reference
        # if self.wallet_account_number:
        #     return {
        #         'success': False,
        #         'account_number': self.wallet_account_number,
        #         'message': 'Wallet already exists for this partner',
        #         'errors': ['Wallet already created']
        #     }
        #
        # # Get data from partner
        # wallet_bvn = bvn or self.bvn
        # wallet_phone = phone or self.phone or self.mobile
        #
        # if not wallet_bvn:
        #     raise ValidationError(_("BVN is required for wallet creation."))
        #
        # if not wallet_phone:
        #     raise ValidationError(_("Phone number is required for wallet creation."))
        #
        # # Extract name parts
        # if self.name:
        #     name_parts = self.name.split(' ', 1)
        #     firstname = name_parts[0]
        #     lastname = name_parts[1] if len(name_parts) > 1 else ''
        # else:
        #     firstname = ''
        #     lastname = ''
        #
        # # Format date of birth
        # dob = '1990-01-01'  # Default if not found
        # # Check if birthdate field exists (common in odoo)
        # if hasattr(self, 'birthdate') and self.birthdate:
        #     dob = str(self.birthdate)
        # elif hasattr(self, 'date_of_birth') and self.date_of_birth:
        #     dob = str(self.date_of_birth)
        #
        # # Call BaaS service
        baas_service = self.env['baas.service']
        result = baas_service.create_tier_two_wallet(
            firstname=firstname,
            lastname=lastname,
            phone=wallet_phone,
            dob=dob,
            bvn=wallet_bvn
        )
        
        if result['success']:
            self.write({
                'wallet_account_number': result['account_number'],
                'wallet_tier': 'tier_2',
                'wallet_status': 'active',
                'wallet_created_date': fields.Datetime.now()
            })
            
        return result

    def action_create_wallet_tier_two(self):
        """Action method to create Tier 2 wallet with user feedback"""
        self.ensure_one()
        
        if self.wallet_account_number:
            raise ValidationError(_("Wallet already exists: %s") % self.wallet_account_number)
            
        result = self.create_wallet_tier_two()
        
        if result['success']:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Tier 2 Wallet created successfully! Account: %s') % result['account_number'],
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                }
            }
        else:
            error_msg = result.get('message', 'Failed to create wallet')
            errors = result.get('errors', [])
            if errors:
                error_msg += '\n' + '\n'.join(errors)
            raise ValidationError(_('Wallet Creation Failed:\n%s') % error_msg)

    # backwards compatibility wrappers for the original tier‑one names
    def create_wallet_tier_one(self, bvn=None, phone=None):
        _logger.warning("create_wallet_tier_one() is deprecated; use tier_two variant")
        return self.create_wallet_tier_two(bvn=bvn, phone=phone)

    def action_create_wallet_tier_one(self):
        _logger.warning("action_create_wallet_tier_one() is deprecated; use tier_two variant")
        return self.action_create_wallet_tier_two()

    # def create_wallet_tier_three(self, bvn=None, nin=None):
    #     """Create Tier Three wallet for this partner with full KYC
    #     
    #     :param bvn: Bank Verification Number
    #     :param nin: National Identification Number
    #     :return: dict with creation result
    #     """
    #     self.ensure_one()
    #     
    #     if self.wallet_account_number:
    #         return {
    #             'success': False,
    #             'account_number': self.wallet_account_number,
    #             'message': 'Wallet already exists for this partner',
    #             'errors': ['Wallet already created'],
    #             'full_response': None
    #         }
    #         
    #     # Get data from partner
    #     wallet_bvn = bvn or self.bvn
    #     wallet_nin = nin or self.nin
    #     
    #     if not wallet_bvn:
    #         raise ValidationError(_("BVN is required for Tier 3 wallet creation."))
    #         
    #     if not self.utility_bill:
    #         raise ValidationError(_("Utility bill image is required for Tier 3 wallet creation."))
    #         
    #     # Extract name parts
    #     if self.name:
    #         name_parts = self.name.split(' ', 1)
    #         firstname = name_parts[0]
    #         lastname = name_parts[1] if len(name_parts) > 1 else ''
    #     else:
    #         firstname = ''
    #         lastname = ''
    #         
    #     # Format date of birth
    #     dob = '1990-01-01'  # Default if not found
    #     # Check if birthdate field exists (common in odoo)
    #     if hasattr(self, 'birthdate') and self.birthdate:
    #         dob = str(self.birthdate)
    #     elif hasattr(self, 'date_of_birth') and self.date_of_birth:
    #         dob = str(self.date_of_birth)
    #         
    #     phone = self.phone or self.mobile
    #     if not phone:
    #          raise ValidationError(_("Phone number is required for wallet creation."))

    #     # Map address fields
    #     address = self.street or ''
    #     if self.street2:
    #         address += f", {self.street2}"
    #         
    #     city = self.city or ''
    #     state = self.state_id.name or ''
    #     country = self.country_id.name or 'Nigeria'
    #     postal_code = self.zip or ''
    #     lga = self.lga or ''
    #     
    #     if not all([address, city, state, lga]):
    #         raise ValidationError(_("Complete address (Street, City, State, and LGA) is required for Tier 3 wallet."))

    #     # Call BaaS service
    #     baas_service = self.env['baas.service']
    #     result = baas_service.create_tier_three_wallet(
    #         firstname=firstname,
    #         lastname=lastname,
    #         phone=phone,
    #         dob=dob,
    #         bvn=wallet_bvn,
    #         nin=wallet_nin,
    #         address=address,
    #         city=city,
    #         state=state,
    #         country=country,
    #         postal_code=postal_code,
    #         lga=lga,
    #         utility_bill=self.utility_bill,
    #         utility_bill_name=self.utility_bill_name
    #     )
    #     
    #     if result['success']:
    #         vals = {
    #             'wallet_tier': 'tier_3',
    #             'wallet_created_date': fields.Datetime.now(),
    #         }
    #         if result.get('account_number'):
    #             vals.update({
    #                 'wallet_account_number': result['account_number'],
    #                 'wallet_status': 'active',
    #                 'wallet_creation_status': 'COMPLETED',
    #             })
    #         else:
    #             vals.update({
    #                 'wallet_creation_reference': result.get('reference'),
    #                 'wallet_creation_status': 'PENDING',
    #             })
    #         self.write(vals)
    #         
    #     return result

    # def action_create_wallet_tier_three(self):
    #     """Action method to create Tier 3 wallet with user feedback"""
    #     self.ensure_one()
    #     
    #     if self.wallet_account_number:
    #         raise ValidationError(_("Wallet already exists: %s") % self.wallet_account_number)
    #         
    #     result = self.create_wallet_tier_three()
    #     
    #     if result['success']:
    #         message = _('Tier 3 Wallet request submitted successfully!')
    #         if result.get('account_number'):
    #             message = _('Tier 3 Wallet created successfully! Account: %s') % result['account_number']
    #         else:
    #             message = _('Tier 3 Wallet creation is pending. Reference: %s') % result.get('reference')
    #             
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': _('Success'),
    #                 'message': message,
    #                 'type': 'success',
    #                 'sticky': False,
    #                 'next': {'type': 'ir.actions.client', 'tag': 'reload'},
    #             }
    #         }
    #     else:
    #         error_msg = result.get('message', 'Failed to create Tier 3 wallet')
    #         errors = result.get('errors', [])
    #         if errors:
    #             error_msg += '\n' + '\n'.join(errors)
    #         raise ValidationError(_('Wallet Creation Failed:\n%s') % error_msg)

    # def action_check_wallet_tier_three_status(self):
    #     """Action method to manually check the status of a pending Tier 3 wallet creation"""
    #     self.ensure_one()
    #     
    #     if not self.wallet_creation_reference:
    #         raise ValidationError(_("No wallet creation reference found for this partner."))
    #         
    #     baas_service = self.env['baas.service']
    #     result = baas_service.get_tier_three_status(self.wallet_creation_reference)
    #     
    #     if result.get('success'):
    #         status = result.get('status')
    #         account_number = result.get('account_number')
    #         
    #         vals = {'wallet_creation_status': status}
    #         if account_number:
    #             vals.update({
    #                 'wallet_account_number': account_number,
    #                 'wallet_status': 'active',
    #             })
    #         self.write(vals)
    #         
    #         # Notify external system if completed
    #         if status == 'COMPLETED' and account_number:
    #             baas_service.notify_external_system(
    #                 action='WALLET_READY',
    #                 subject=_('Wallet Ready for %s') % self.name,
    #                 partner_id=self.id
    #             )
    #         
    #         msg = _('Status: %s') % status
    #         if account_number:
    #             msg += _('\nAccount Number: %s') % account_number
    #             
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': _('Status Update'),
    #                 'message': msg,
    #                 'type': 'success',
    #                 'sticky': False,
    #                 'next': {'type': 'ir.actions.client', 'tag': 'reload'},
    #             }
    #         }
    #     else:
    #         error_msg = result.get('message', 'Failed to retrieve wallet status')
    #         raise ValidationError(_('Status Check Failed:\n%s') % error_msg)

    @api.depends('wallet_account_number')
    def _compute_wallet_balance(self):
        """Compute wallet balance by fetching from BaaS API"""
        for partner in self:
            if partner.wallet_account_number:
                try:
                    baas_service = self.env['baas.service']
                    result = baas_service.get_wallet_balance(partner.wallet_account_number)
                    
                    if result.get('success'):
                        partner.wallet_balance = result.get('balance', 0.0)
                        
                        # Find currency by name/code
                        currency_code = result.get('currency', 'NGN')
                        currency = self.env['res.currency'].sudo().search([
                            '|', ('name', '=', currency_code), ('symbol', '=', currency_code)
                        ], limit=1)
                        if currency:
                            partner.wallet_currency_id = currency.id
                            
                        partner.wallet_balance_last_updated = fields.Datetime.now()
                    else:
                        partner.wallet_balance = 0.0
                except Exception as e:
                    _logger.error("Error fetching wallet balance for partner %s: %s", partner.id, str(e))
                    partner.wallet_balance = 0.0
            else:
                partner.wallet_balance = 0.0

    def action_refresh_wallet_balance(self):
        """Action method to manually refresh wallet balance"""
        self.ensure_one()
        
        if not self.wallet_account_number:
            raise ValidationError(_("No wallet account number found for this partner."))
        
        baas_service = self.env['baas.service']
        result = baas_service.get_wallet_balance(self.wallet_account_number)
        
        if result.get('success'):
            # Trigger recomputation
            self._compute_wallet_balance()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _(
                        'Wallet balance refreshed successfully!\n'
                        'Balance: %s %s'
                    ) % (result.get('balance', 0.0), result.get('currency', 'NGN')),
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                }
            }
        else:
            error_msg = result.get('message', 'Failed to refresh wallet balance')
            raise ValidationError(_('Failed to refresh wallet balance:\n%s') % error_msg)

    # @api.model
    # def cron_check_pending_tier_three_wallets(self):
    #     """Cron job to automatically check status of pending Tier 3 wallets"""
    #     _logger.info("Starting cron to check pending Tier 3 wallets")
    #     pending_partners = self.sudo().search([
    #         ('wallet_creation_status', '=', 'PENDING'),
    #         ('wallet_creation_reference', '!=', False),
    #         ('wallet_account_number', '=', False)
    #     ])
    #     
    #     if not pending_partners:
    #         _logger.info("No pending Tier 3 wallets found")
    #         return
    #         
    #     baas_service = self.env['baas.service']
    #     for partner in pending_partners:
    #         try:
    #             _logger.info("Checking status for partner %s (Ref: %s)", partner.id, partner.wallet_creation_reference)
    #             result = baas_service.get_tier_three_status(partner.wallet_creation_reference)
    #             
    #             if result.get('success'):
    #                 status = result.get('status')
    #                 account_number = result.get('account_number')
    #                 
    #                 if status == 'COMPLETED' and account_number:
    #                     partner.write({
    #                         'wallet_account_number': account_number,
    #                         'wallet_status': 'active',
    #                         'wallet_creation_status': 'COMPLETED'
    #                     })
    #                     # Notify external system
    #                     baas_service.notify_external_system(
    #                         action='WALLET_READY',
    #                         subject=_('Wallet Ready for %s') % partner.name,
    #                         partner_id=partner.id
    #                     )
    #                     _logger.info("Wallet activated and notified for partner %s", partner.id)
    #                 elif status in ['FAILED', 'REJECTED']:
    #                     partner.write({'wallet_creation_status': status})
    #                     _logger.warning("Wallet creation %s for partner %s", status, partner.id)
    #             else:
    #                 _logger.error("Failed to check status for partner %s: %s", partner.id, result.get('message'))
    #         except Exception as e:
    #             _logger.error("Error in Tier 3 cron for partner %s: %s", partner.id, str(e))
