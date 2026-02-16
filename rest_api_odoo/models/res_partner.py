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
    wallet_balance = fields.Monetary(
        string='Wallet Balance',
        compute='_compute_wallet_balance',
        currency_field='wallet_currency',
        help='Current wallet balance (fetched from BaaS API)',
        store=False
    )
    wallet_currency = fields.Char(
        string='Wallet Currency',
        default='NGN',
        help='Currency code for wallet balance'
    )
    wallet_balance_last_updated = fields.Datetime(
        string='Balance Last Updated',
        help='Last time wallet balance was fetched'
    )

    def create_wallet_tier_one(self, bvn=None):
        """Create Tier One wallet for this partner using BVN
        
        :param bvn: Bank Verification Number (optional, uses partner's BVN if not provided)
        :return: dict with creation result containing success, account_number, message, errors
        :raises: ValidationError if required data is missing
        """
        self.ensure_one()
        
        # Check if wallet already exists
        if self.wallet_account_number:
            return {
                'success': False,
                'account_numbeaccount_numberr': self.wallet_account_number,
                'message': 'Wallet already exists for this partner',
                'errors': ['Wallet already created'],
                'full_response': None
            }
        
        # ====================e====================================================
        # TEST DATA FOR BAAS TESTING (COMMENT OUT FOR PRODUCTION)
        # ========================================================================
        # Use hardcoded test data that BaaS test environment accepts
        wallet_bvn = "22200011111"  # test BVN
        firstname = "John"           # test first name
        lastname = "Doe"             # test last name
        phone = "7060514527"     # test phone number
        dob = "1990-01-15"           # test date of birth
        # ========================================================================
        
        # ========================================================================
        # PRODUCTION CODE (UNCOMMENT FOR PRODUCTION, COMMENT OUT TEST DATA ABOVE)
        # ========================================================================
        # # Use provided BVN or try to get from partner
        # wallet_bvn = bvn
        # 
        # # Try to get BVN from partner if available
        # if not wallet_bvn and hasattr(self, 'bvn'):
        #     wallet_bvn = self.bvn
        # 
        # if not wallet_bvn:
        #     raise ValidationError(_("BVN is required to create a wallet."))
        # 
        # # Extract firstname and lastname
        # if self.name:
        #     name_parts = self.name.split(' ', 1)
        #     firstname = name_parts[0] if name_parts else self.name
        #     lastname = name_parts[1] if len(name_parts) > 1 else ''
        # else:
        #     firstname = getattr(self, 'firstname', '') or ''
        #     lastname = getattr(self, 'lastname', '') or ''
        # 
        # if not firstname:
        #     raise ValidationError(_("First name is required to create a wallet."))
        # 
        # phone = self.phone or self.mobile
        # if not phone:
        #     raise ValidationError(_("Phone number is required to create a wallet."))
        # 
        # # Get date of birth (default if not available)
        # dob = '1990-01-01'  # Default
        # if hasattr(self, 'birthdate') and self.birthdate:
        #     if isinstance(self.birthdate, fields.Date):
        #         dob = self.birthdate.strftime('%Y-%m-%d')
        #     else:
        #         dob = str(self.birthdate)
        # ========================================================================
        
        # Call BaaS service
        baas_service = self.env['baas.service']
        result = baas_service.create_tier_one_wallet(
            firstname=firstname,
            lastname=lastname,
            phone=phone,
            dob=dob,
            bvn=wallet_bvn
        )
        
        if result['success']:
            # Update partner with wallet information
            self.write({
                'wallet_account_number': result['account_number'],
                'wallet_tier': 'tier_1',
                'wallet_status': 'active',
                'wallet_created_date': fields.Datetime.now(),
            })
        
        return result

    def action_create_wallet_tier_one(self):
        """Action method to create wallet with user feedback"""
        self.ensure_one()
        
        # Check if wallet already exists
        if self.wallet_account_number:
            raise ValidationError(_(
                "Wallet already exists for this partner.\n"
                "Account Number: %s"
            ) % self.wallet_account_number)
        
        # Create wallet
        result = self.create_wallet_tier_one()
        
        if result['success']:
            # Show success message
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _(
                        'Wallet created successfully!\n'
                        'Account Number: %s'
                    ) % result['account_number'],account_number
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            # Show error message
            error_msg = result.get('message', 'Failed to create wallet')
            errors = result.get('errors', [])
            if errors:
                error_msg += '\n' + '\n'.join(errors)
            raise ValidationError(_('Wallet Creation Failed:\n%s') % error_msg)
account_number
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
                        partner.wallet_currency = result.get('currency', 'NGN')
                        partner.wallet_balance_last_updated = fields.Datetime.now()
                    else:
                        partner.wallet_balance = 0.0
                        partner.wallet_currency = 'NGN'
                except Exception as e:
                    _logger.error("Error fetching wallet balance for partner %s: %s", partner.id, str(e))
                    partner.wallet_balance = 0.0
                    partner.wallet_currency = 'NGN'
            else:
                partner.wallet_balance = 0.0
                partner.wallet_currency = 'NGN'

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
                }
            }
        else:
            error_msg = result.get('message', 'Failed to refresh wallet balance')
            raise ValidationError(_('Failed to refresh wallet balance:\n%s') % error_msg)
