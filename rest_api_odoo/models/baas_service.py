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
            'webhook_secret': ir_config.get_param('baas.webhook_secret', ''),
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
        """Create a Tier One wallet via BaaS API
        
        :param firstname: Customer first name
        :param lastname: Customer last name
        :param phone: Phone number
        :param dob: Date of birth (YYYY-MM-DD format)
        :param bvn: Bank Verification Number
        :return: dict with success, account_number, message, errors
        """
        if not all([firstname, lastname, phone, dob, bvn]):
            return {
                'success': False,
                'account_number': None,
                'message': 'Missing required parameters',
                'errors': ['Firstname, lastname, phone, dob, and bvn are required']
            }
        
        config = self._get_baas_config()
        try:
            access_token = self._get_access_token()
        except ValidationError as e:
            return {
                'success': False,
                'account_number': None,
                'message': str(e),
                'errors': [str(e)]
            }

        # url = f"{config['base_url']}/wallet/create"  # Old endpoint
        url = f"{config['base_url']}/wallet/create-tier-2"  # Corrected pattern
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Authorization': f'Bearer {access_token}'
        }
        
        payload = {
            'firstname': firstname,
            'lastname': lastname,
            'phone': phone,
            'dob': dob,
            'bvn': str(bvn)
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            _logger.info(
                "BaaS Wallet Creation Response: Status %s, Body: %s",
                response.status_code,
                response.text[:500]
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') == 'SUCCESS':
                data = result.get('data', {})
                account_number = data.get('accountNumber')
                return {
                    'success': True,
                    'account_number': account_number,
                    'message': result.get('message', 'success'),
                    'errors': [],
                    'full_response': result
                }
            else:
                messages = result.get('messages', [])
                error_msg = '; '.join(messages) if messages else result.get('message', 'Failed to create wallet')
                return {
                    'success': False,
                    'account_number': None,
                    'message': error_msg,
                    'errors': result.get('errors', [error_msg]),
                    'full_response': result
                }
                
        except requests.exceptions.RequestException as e:
            _logger.error("BaaS Wallet Creation Error: %s", str(e))
            return {
                'success': False,
                'account_number': None,
                'message': f"API request failed: {str(e)}",
                'errors': [str(e)]
            }
        except Exception as e:
            _logger.error("BaaS Wallet Creation Unexpected Error: %s", str(e))
            return {
                'success': False,
                'account_number': None,
                'message': f"Unexpected error: {str(e)}",
                'errors': [str(e)]
            }

    # ------------------------------------------------------------------
    # Tier‑two helpers (the existing "tier one" logic is reused but points
    # at a different endpoint and writes a different tier value).
    # ------------------------------------------------------------------
    def create_tier_two_wallet(self, firstname, lastname, phone, dob, bvn, nin=None):
        """Create a Tier Two wallet via BaaS API
        :param firstname: Customer first name
        :param lastname: Customer last name
        :param phone: Phone number
        :param dob: Date of birth (YYYY-MM-DD format)
        :param bvn: Bank Verification Number
        :param nin: National Identification Number
        :return: dict with success, account_number, message, errors
        """
        # payload validation identical to tier‑one
        if not all([firstname, lastname, phone, dob, bvn]):
            return {
                'success': False,
                'account_number': None,
                'message': 'Missing required parameters',
                'errors': ['Firstname, lastname, phone, dob, and bvn are required']
            }

        config = self._get_baas_config()
        try:
            access_token = self._get_access_token()
        except ValidationError as e:
            return {
                'success': False,
                'account_number': None,
                'message': str(e),
                'errors': [str(e)]
            }

        # url = f"{config['base_url']}/wallet/create-tier-two"
        # url = f"{config['base_url']}/wallet/create-tier-2"
        url = f"{config['base_url']}/wallet/create-tier-1"  # Temporary fix using working Tier 1 endpoint
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Authorization': f'Bearer {access_token}'
        }
        payload = {
            'firstname': firstname,
            'lastname': lastname,
            'phone': phone,
            'dob': dob,
            'bvn': str(bvn),
            'nin': str(nin) if nin else None,
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            _logger.info(
                "BaaS Tier 2 Wallet Creation (via /wallet/create) Response: Status %s, Body: %s",
                response.status_code,
                response.text[:500]
            )
            response.raise_for_status()
            result = response.json()
            if result.get('status') == 'SUCCESS':
                data = result.get('data', {})
                account_number = data.get('accountNumber')
                return {
                    'success': True,
                    'account_number': account_number,
                    'message': result.get('message', 'success'),
                    'errors': [],
                    'full_response': result
                }
            else:
                messages = result.get('messages', [])
                error_msg = '; '.join(messages) if messages else result.get('message', 'Failed to create wallet')
                return {
                    'success': False,
                    'account_number': None,
                    'message': error_msg,
                    'errors': result.get('errors', [error_msg]),
                    'full_response': result
                }
        except requests.exceptions.RequestException as e:
            _logger.error("BaaS Tier 2 Wallet Creation Error: %s", str(e))
            return {
                'success': False,
                'account_number': None,
                'message': f"API request failed: {str(e)}",
                'errors': [str(e)]
            }
        except Exception as e:
            _logger.error("BaaS Tier 2 Wallet Creation Unexpected Error: %s", str(e))
            return {
                'success': False,
                'account_number': None,
                'message': f"Unexpected error: {str(e)}",
                'errors': [str(e)]
            }

    def get_tier_two_status(self, account_number):
        """Check status of a tier‑two wallet by account number"""
        if not account_number:
            return {'success': False, 'status': 'FAILED', 'message': 'Account number is required', 'errors': ['Account number is required']}
        config = self._get_baas_config()
        try:
            access_token = self._get_access_token()
        except ValidationError as e:
            return {'success': False, 'status': 'ERROR', 'message': str(e), 'errors': [str(e)]}
        url = f"{config['base_url']}/wallet/tier-two-status"
        params = {'account_number': account_number}
        headers = {
            'Accept': '*/*',
            'Authorization': f'Bearer {access_token}'
        }
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            _logger.info("BaaS Tier 2 Status Check: %s", response.text[:500])
            response.raise_for_status()
            result = response.json()
            if result.get('status') == 'SUCCESS':
                data = result.get('data', {})
                return {'success': True, 'status': data.get('status'), 'account_number': data.get('accountNumber'), 'message': result.get('message', '')}
            else:
                return {'success': False, 'status': 'ERROR', 'message': result.get('message', ''), 'errors': result.get('errors', [])}
        except Exception as e:
            _logger.error("BaaS Tier 2 Status Error: %s", str(e))
            return {'success': False, 'status': 'ERROR', 'message': f"Request failed: {str(e)}", 'errors': [str(e)]}

    # def create_tier_three_wallet(self, firstname, lastname, phone, dob, bvn, nin, address, city, state, country, postal_code, lga, utility_bill, utility_bill_name):
    #     """Create a Tier Three wallet with full KYC documentation
    #     
    #     :param firstname: Customer first name
    #     :param lastname: Customer last name
    #     :param phone: Phone number
    #     :param dob: Date of birth (YYYY-MM-DD format)
    #     :param bvn: Bank Verification Number
    #     :param nin: National Identification Number
    #     :param address: Physical address
    #     :param city: City
    #     :param state: State
    #     :param country: Country
    #     :param postal_code: Postal code
    #     :param lga: Local Government Area
    #     :param utility_bill: Utility bill file content (bytes or base64)
    #     :param utility_bill_name: Utility bill filename
    #     :return: dict with success, account_number, message, errors, full_response
    #     """
    #     if not all([firstname, lastname, phone, dob, bvn, address, city, state, lga, utility_bill]):
    #         return {
    #             'success': False,
    #             'account_number': None,
    #             'message': 'Missing required parameters for Tier 3 wallet',
    #             'errors': ['All KYC parameters and utility bill are required'],
    #             'full_response': None
    #         }
    #         
    #     import base64
    #     import io
    #     
    #     # Ensure utility_bill is bytes
    #     if isinstance(utility_bill, str):
    #         try:
    #             utility_bill_bytes = base64.b64decode(utility_bill)
    #         except Exception:
    #             utility_bill_bytes = utility_bill.encode('utf-8')
    #     else:
    #         utility_bill_bytes = utility_bill

    #     config = self._get_baas_config()
    #     try:
    #         access_token = self._get_access_token()
    #     except ValidationError as e:
    #         return {
    #             'success': False,
    #             'account_number': None,
    #             'message': str(e),
    #             'errors': [str(e)],
    #             'full_response': None
    #         }

    #     url = f"{config['base_url']}/wallet/create-tier-3"
    #     
    #     headers = {
    #         'Accept': '*/*',
    #         'Authorization': f'Bearer {access_token}'
    #     }
    #     
    #     # For multipart/form-data, we use 'data' for fields and 'files' for files
    #     payload = {
    #         'firstname': firstname.strip(),
    #         'lastname': lastname.strip(),
    #         'phone': phone.strip(),
    #         'dob': dob.strip(),
    #         'bvn': str(bvn).strip(),
    #         'nin': str(nin or '').strip(),
    #         'address': address.strip(),
    #         'city': city.strip(),
    #         'state': state.strip(),
    #         'country': country.strip(),
    #         'postalCode': str(postal_code or '').strip(),
    #         'lga': lga.strip()
    #     }
    #     
    #     files = {
    #         'utilityBillImage': (utility_bill_name or 'utility_bill.jpg', utility_bill_bytes, 'image/jpeg')
    #     }
    #     
    #     try:
    #         response = requests.post(
    #             url,
    #             data=payload,
    #             files=files,
    #             headers=headers,
    #             timeout=60  # Increased timeout for file upload
    #         )
    #         
    #         _logger.info(
    #             "BaaS Tier 3 Wallet Creation Response: Status %s, Body: %s",
    #             response.status_code,
    #             response.text[:500]
    #         )
    #         
    #         response.raise_for_status()
    #         result = response.json()
    #         
    #         if result.get('status') == 'SUCCESS':
    #             data = result.get('data', {})
    #             account_number = data.get('accountNumber')
    #             reference = data.get('reference')
    #             return {
    #                 'success': True,
    #                 'account_number': account_number,
    #                 'reference': reference,
    #                 'message': result.get('message', 'Tier 3 wallet request submitted successfully'),
    #                 'errors': [],
    #                 'full_response': result
    #             }
    #         else:
    #             messages = result.get('messages', [])
    #             error_msg = '; '.join(messages) if messages else result.get('message', 'Failed to create Tier 3 wallet')
    #             return {
    #                 'success': False,
    #                 'account_number': None,
    #                 'message': error_msg,
    #                 'errors': result.get('errors', [error_msg]),
    #                 'full_response': result
    #             }
    #             
    #     except requests.exceptions.RequestException as e:
    #         _logger.error("BaaS Tier 3 Wallet Creation Error: %s", str(e))
    #         return {
    #             'success': False,
    #             'account_number': None,
    #             'message': f"API request failed: {str(e)}",
    #             'errors': [str(e)],
    #             'full_response': None
    #         }
    #     except Exception as e:
    #         _logger.error("BaaS Tier 3 Wallet Creation Unexpected Error: %s", str(e))
    #         return {
    #             'success': False,
    #             'account_number': None,
    #             'message': f"Unexpected error: {str(e)}",
    #             'errors': [str(e)],
    #             'full_response': None
    #         }

    def get_wallet_balance(self, account_number):
        """Get wallet balance/summary from BaaS API
        
        :param account_number: Wallet account number
        :return: dict with success, balance, currency, and other wallet details
        """
        if not account_number:
            return {
                'success': False,
                'balance': None,
                'currency': None,
                'message': 'Account number is required',
                'errors': ['Account number is required']
            }
        
        config = self._get_baas_config()
        
        try:
            access_token = self._get_access_token()
        except ValidationError as e:
            return {
                'success': False,
                'balance': None,
                'currency': None,
                'message': str(e),
                'errors': [str(e)]
            }
        
        # Using the account details endpoint for absolute ledger balance accuracy
        url = f"{config['base_url']}/wallet/account?walletAccountId={account_number}&details=true"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') == 'SUCCESS':
                data = result.get('data', {})
                # Use availableBalance or accountBalance which shows the true ledger status
                balance = data.get('availableBalance') or data.get('accountBalance', 0.0)
                currency = data.get('currency', 'NGN')
                
                return {
                    'success': True,
                    'balance': float(balance) if balance is not None else 0.0,
                    'currency': currency,
                    'account_number': account_number,
                    'data': data,
                    'message': result.get('message', 'Balance retrieved successfully'),
                    'errors': []
                }
            else:
                errors = result.get('errors', [])
                messages = result.get('messages', [])
                error_msg = '; '.join(messages) if messages else result.get('message', 'Failed to get wallet balance')
                
                return {
                    'success': False,
                    'balance': None,
                    'currency': None,
                    'message': error_msg,
                    'errors': errors if errors else [error_msg]
                }
                
        except requests.exceptions.Timeout:
            _logger.error("BaaS Wallet Balance Error: Request timeout")
            return {
                'success': False,
                'balance': None,
                'currency': None,
                'message': 'Request to BaaS API timed out',
                'errors': ['Request timeout']
            }
        except requests.exceptions.ConnectionError as e:
            _logger.error("BaaS Wallet Balance Error: Connection failed - %s", str(e))
            return {
                'success': False,
                'balance': None,
                'currency': None,
                'message': 'Failed to connect to BaaS API',
                'errors': ['Connection error']
            }
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg = error_data.get('message', error_msg)
                errors = error_data.get('errors', [])
            except (ValueError, KeyError):
                errors = [error_msg]
            
            _logger.error("BaaS Wallet Balance Error: %s", error_msg)
            
            return {
                'success': False,
                'balance': None,
                'currency': None,
                'message': error_msg,
                'errors': errors
            }
        except Exception as e:
            _logger.error("BaaS Wallet Balance Error: %s", str(e))
            return {
                'success': False,
                'balance': None,
                'currency': None,
                'message': f"Error: {str(e)}",
                'errors': [str(e)]
            }
    def debit_wallet(self, account_number, amount, reference):
        """Debit a wallet via BaaS API
        
        :param account_number: Wallet account number
        :param amount: Amount to debit
        :param reference: Transaction reference
        :return: dict with success, transaction_id, message, and errors
        """
        if not all([account_number, amount, reference]):
            return {
                'success': False,
                'transaction_id': None,
                'message': 'Missing required parameters',
                'errors': ['Account number, amount, and reference are required']
            }
        
        config = self._get_baas_config()
        
        try:
            access_token = self._get_access_token()
        except ValidationError as e:
            return {
                'success': False,
                'transaction_id': None,
                'message': str(e),
                'errors': [str(e)]
            }
        
        # NOTE: Endpoint /wallet/debit is assumed based on common BaaS patterns
        # Adjust if the actual API uses a different endpoint or method
        url = f"{config['base_url']}/wallet/debit"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Authorization': f'Bearer {access_token}'
        }
        
        payload = {
            'accountNumber': account_number,
            'amount': amount,
            'reference': reference,
            'channel': 'LOAN_REPAYMENT'
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            _logger.info(
                "BaaS Wallet Debit Response: Status %s, Body: %s",
                response.status_code,
                response.text[:500]
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') == 'SUCCESS':
                data = result.get('data', {})
                transaction_id = data.get('transactionId') or data.get('id')
                
                return {
                    'success': True,
                    'transaction_id': transaction_id,
                    'message': result.get('message', 'Debit successful'),
                    'errors': [],
                    'full_response': result
                }
            else:
                messages = result.get('messages', [])
                error_msg = '; '.join(messages) if messages else result.get('message', 'Failed to debit wallet')
                return {
                    'success': False,
                    'transaction_id': None,
                    'message': error_msg,
                    'errors': result.get('errors', [error_msg]),
                    'full_response': result
                }
                
        except requests.exceptions.RequestException as e:
            _logger.error("BaaS Wallet Debit Error: %s", str(e))
            return {
                'success': False,
                'transaction_id': None,
                'message': f"API request failed: {str(e)}",
                'errors': [str(e)]
            }
        except Exception as e:
            _logger.error("BaaS Wallet Debit Error: Unexpected error - %s", str(e))
            return {
                'success': False,
                'transaction_id': None,
                'message': f"Unexpected error: {str(e)}",
                'errors': [str(e)]
            }

    def get_transaction_details(self, transaction_id):
        """Get transaction details from BaaS API for verification
        
        :param transaction_id: The transaction ID/reference to check
        :return: dict with success, amount, account_number, status, message
        """
        if not transaction_id:
            return {'success': False, 'message': 'Transaction ID is required'}
            
        config = self._get_baas_config()
        try:
            access_token = self._get_access_token()
        except ValidationError as e:
            return {'success': False, 'message': str(e)}

        # Using the receipt/status endpoint pattern from Postman
        url = f"{config['base_url']}/wallet/transaction/{transaction_id}"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            _logger.info("BaaS Transaction Status Response [%s]: %s", transaction_id, response.text[:500])
            
            # If 404, transaction might not exist yet or wrong endpoint
            if response.status_code == 404:
                return {'success': False, 'message': 'Transaction not found'}
                
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') == 'SUCCESS':
                data = result.get('data', {})
                return {
                    'success': True,
                    'amount': float(data.get('amount') or 0.0),
                    'account_number': data.get('accountNumber') or data.get('toAccountNumber'),
                    'status': data.get('status'), # e.g. 'SUCCESSFUL', 'PENDING'
                    'message': 'Transaction details retrieved'
                }
            else:
                return {'success': False, 'message': result.get('message', 'Failed to retrieve transaction')}
                
        except Exception as e:
            _logger.error("BaaS Transaction Detail Error [%s]: %s", transaction_id, str(e))
            return {'success': False, 'message': f"Request failed: {str(e)}"}

    # def get_tier_three_status(self, reference):
    #     """Check the status of a Tier Three wallet creation request
    #     
    #     :param reference: Submission reference from creation request
    #     :return: dict with success, status, account_number, message, errors
    #     """
    #     if not reference:
    #         return {
    #             'success': False,
    #             'status': 'FAILED',
    #             'message': 'Reference is required',
    #             'errors': ['Reference is required']
    #         }
    # 
    #     config = self._get_baas_config()
    #     try:
    #         access_token = self._get_access_token()
    #     except ValidationError as e:
    #         return {
    #             'success': False,
    #             'status': 'ERROR',
    #             'message': str(e),
    #             'errors': [str(e)]
    #         }
    # 
    #     url = f"{config['base_url']}/wallet/tier-3-status"
    #     params = {'reference': reference}
    #     
    #     headers = {
    #         'Accept': '*/*',
    #         'Authorization': f'Bearer {access_token}'
    #     }
    # 
    #     try:
    #         response = requests.get(
    #             url,
    #             params=params,
    #             headers=headers,
    #             timeout=30
    #         )
    #         
    #         _logger.info(
    #             "BaaS Tier 3 Status Check: Status %s, Body: %s",
    #             response.status_code,
    #             response.text[:500]
    #         )
    #         
    #         response.raise_for_status()
    #         result = response.json()
    #         
    #         if result.get('status') == 'SUCCESS':
    #             data = result.get('data', {})
    #             # Possible statuses: PENDING, APPROVED, REJECTED, COMPLETED
    #             status = data.get('status', 'PENDING')
    #             account_number = data.get('accountNumber')
    #             
    #             return {
    #                 'success': True,
    #                 'status': status,
    #                 'account_number': account_number,
    #                 'message': result.get('message', 'Status retrieved successfully'),
    #                 'data': data
    #             }
    #         else:
    #             return {
    #                 'success': False,
    #                 'status': 'ERROR',
    #                 'message': result.get('message', 'Failed to retrieve status'),
    #                 'errors': result.get('errors', [])
    #             }
    #             
    #     except Exception as e:
    #         _logger.error("BaaS Tier 3 Status Error: %s", str(e))
    #         return {
    #             'success': False,
    #             'status': 'ERROR',
    #             'message': f"Request failed: {str(e)}",
    #             'errors': [str(e)]
    #         }

    def notify_external_system(self, action, subject, partner_id, content=None, loan_id=None):
        """Centralized method to notify external systems (Frontend/Backend)
        
        :param action: Action string (e.g. 'WALLET_READY')
        :param subject: Human readable subject
        :param partner_id: ID of the partner related to the notification
        :param content: Additional data dict
        :param loan_id: Optional loan ID if applicable
        """
        ir_config = self.env['ir.config_parameter'].sudo()
        frontend_url = ir_config.get_param('caixa.frontend_notify_url')
        api_key = ir_config.get_param('caixa.frontend_api_key')
        
        if not frontend_url:
            _logger.warning("Notification skipped: caixa.frontend_notify_url not configured")
            return False
            
        partner = self.env['res.partner'].sudo().browse(partner_id)
        if not partner.exists():
            _logger.error("Notification failed: Partner %s not found", partner_id)
            return False

        payload = {
            "action": action,
            "subject": subject,
            "client_id": partner.id,
            "client_name": partner.name,
            "wallet_account_number": partner.wallet_account_number,
            "wallet_tier": partner.wallet_tier,
            "content": content or {},
            "loan_id": loan_id
        }
        
        if loan_id:
            loan = self.env['dev.loan.loan'].sudo().browse(loan_id)
            if loan.exists():
                payload["loan_name"] = loan.name

        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": api_key or ""
        }
        
        endpoint = f"{frontend_url.rstrip('/')}/api/erp/notifications"
        _logger.info("Sending notification to %s for partner %s", endpoint, partner.id)
        
        try:
            response = requests.post(
                endpoint, 
                json=payload, 
                headers=headers,
                timeout=10
            )
            _logger.info("External notification response: %s", response.status_code)
            return response.status_code in (200, 201)
        except Exception as e:
            _logger.error("External notification failed: %s", str(e))
            return False

