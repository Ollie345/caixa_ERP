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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import requests
import logging
from odoo import models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class BaasService(models.AbstractModel):
    """Service class for BaaS API integration"""
    _name = 'baas.service'
    _description = 'BaaS API Service'

    def _get_baas_config(self):
        """Get BaaS configuration from system parameters
        
        :return: dict with base_url, client_id, client_secret
        """
        ir_config = self.env['ir.config_parameter'].sudo()
        return {
            'base_url': ir_config.get_param('baas.base_url', 'https://baas.dev.getrova.co.uk'),
            'client_id': ir_config.get_param('baas.client_id', ''),
            'client_secret': ir_config.get_param('baas.client_secret', ''),
        }

    def _get_access_token(self):
        """Get OAuth2 access token from BaaS API
        
        :return: str access token
        :raises: ValidationError if credentials missing or request fails
        """
        config = self._get_baas_config()
        
        if not config['client_id'] or not config['client_secret']:
            raise ValidationError(_(
                "BaaS credentials not configured. Please set client_id and "
                "client_secret in system parameters (Settings → Technical → "
                "Parameters → System Parameters)."
            ))
        
        token_url = f"{config['base_url']}/token"
        
        payload = {
            'grant_type': 'client_credentials',
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'scope': 'profile'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = requests.post(
                token_url,
                data=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            token_data = response.json()
            access_token = token_data.get('access_token')
            
            if not access_token:
                raise ValidationError(_(
                    "Failed to get access token: No access_token in response"
                ))
            
            return access_token
            
        except requests.exceptions.Timeout:
            _logger.error("BaaS Token Error: Request timeout")
            raise ValidationError(_(
                "BaaS API request timed out. Please check your network "
                "connection and try again."
            ))
        except requests.exceptions.ConnectionError as e:
            _logger.error("BaaS Token Error: Connection failed - %s", str(e))
            raise ValidationError(_(
                "Failed to connect to BaaS API. Please check the base URL "
                "and network connection."
            ))
        except requests.exceptions.HTTPError as e:
            _logger.error("BaaS Token Error: HTTP %s - %s", e.response.status_code, str(e))
            raise ValidationError(_(
                "BaaS API authentication failed (HTTP %s). Please verify your "
                "client_id and client_secret."
            ) % e.response.status_code)
        except requests.exceptions.RequestException as e:
            _logger.error("BaaS Token Error: %s", str(e))
            raise ValidationError(_("Failed to get BaaS access token: %s") % str(e))
        except (ValueError, KeyError) as e:
            _logger.error("BaaS Token Error: Invalid response format - %s", str(e))
            raise ValidationError(_(
                "Invalid response from BaaS API. Please check the API endpoint."
            ))

    def create_tier_one_wallet(self, firstname, lastname, phone, dob, bvn):
        """Create a Tier One wallet with BVN
        
        :param firstname: Customer first name
        :param lastname: Customer last name
        :param phone: Phone number
        :param dob: Date of birth (YYYY-MM-DD format)
        :param bvn: Bank Verification Number
        :return: dict with success, account_number, message, errors, full_response
        """
        # Validate input parameters
        if not all([firstname, lastname, phone, dob, bvn]):
            return {
                'success': False,
                'account_number': None,
                'message': 'Missing required parameters',
                'errors': ['All parameters (firstname, lastname, phone, dob, bvn) are required'],
                'full_response': None
            }
        
        # Validate date format
        try:
            from datetime import datetime
            datetime.strptime(dob, '%Y-%m-%d')
        except ValueError:
            return {
                'success': False,
                'account_number': None,
                'message': 'Invalid date format. Expected YYYY-MM-DD',
                'errors': ['Date of birth must be in YYYY-MM-DD format'],
                'full_response': None
            }
        
        config = self._get_baas_config()
        
        try:
            access_token = self._get_access_token()
        except ValidationError as e:
            return {
                'success': False,
                'account_number': None,
                'message': str(e),
                'errors': [str(e)],
                'full_response': None
            }
        
        url = f"{config['base_url']}/wallet/create-tier-1"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Authorization': f'Bearer {access_token}'
        }
        
        payload = {
            'firstname': firstname.strip(),
            'lastname': lastname.strip(),
            'phone': phone.strip(),
            'dob': dob.strip(),
            'id': {
                'idNumber': str(bvn).strip(),
                'type': 'BVN'
            }
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            # Log response for debugging
            _logger.info(
                "BaaS Wallet Creation Response: Status %s, Body: %s",
                response.status_code,
                response.text[:500]  # Limit log size
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') == 'SUCCESS':
                account_number = result.get('data', {}).get('accountNumber')
                if not account_number:
                    _logger.warning(
                        "BaaS returned SUCCESS but no accountNumber in response: %s",
                        result
                    )
                    return {
                        'success': False,
                        'account_number': None,
                        'message': 'Wallet creation succeeded but no account number returned',
                        'errors': ['Invalid response format from BaaS API'],
                        'full_response': result
                    }
                
                return {
                    'success': True,
                    'account_number': account_number,
                    'message': result.get('message', 'Wallet created successfully'),
                    'errors': [],
                    'full_response': result
                }
            else:
                errors = result.get('errors', [])
                messages = result.get('messages', [])
                error_msg = '; '.join(messages) if messages else result.get('message', 'Failed to create wallet')
                
                return {
                    'success': False,
                    'account_number': None,
                    'message': error_msg,
                    'errors': errors if errors else [error_msg],
                    'full_response': result
                }
                
        except requests.exceptions.Timeout:
            _logger.error("BaaS Wallet Creation Error: Request timeout")
            return {
                'success': False,
                'account_number': None,
                'message': 'Request to BaaS API timed out',
                'errors': ['Request timeout'],
                'full_response': None
            }
        except requests.exceptions.ConnectionError as e:
            _logger.error("BaaS Wallet Creation Error: Connection failed - %s", str(e))
            return {
                'success': False,
                'account_number': None,
                'message': 'Failed to connect to BaaS API',
                'errors': ['Connection error'],
                'full_response': None
            }
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg = error_data.get('message', error_msg)
                errors = error_data.get('errors', [])
            except (ValueError, KeyError):
                errors = [error_msg]
            
            _logger.error(
                "BaaS Wallet Creation Error: %s - %s",
                error_msg,
                e.response.text[:500]
            )
            
            return {
                'success': False,
                'account_number': None,
                'message': error_msg,
                'errors': errors,
                'full_response': None
            }
        except requests.exceptions.RequestException as e:
            _logger.error("BaaS Wallet Creation Error: %s", str(e))
            return {
                'success': False,
                'account_number': None,
                'message': f"API request failed: {str(e)}",
                'errors': [str(e)],
                'full_response': None
            }
        except (ValueError, KeyError) as e:
            _logger.error("BaaS Wallet Creation Error: Invalid response - %s", str(e))
            return {
                'success': False,
                'account_number': None,
                'message': 'Invalid response from BaaS API',
                'errors': ['Invalid response format'],
                'full_response': None
            }
