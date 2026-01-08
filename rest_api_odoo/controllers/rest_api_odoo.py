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
import json
import logging
from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError
from datetime import datetime, date

_logger = logging.getLogger(__name__)


class RestApi(http.Controller):
    """This is a controller which is used to generate responses based on the
    api requests"""

    def auth_api_key(self, api_key):
        """This function is used to authenticate the api-key when sending a
        request"""
        user_id = request.env['res.users'].sudo().search([('api_key', '=', api_key)])
        if api_key is not None and user_id:
             response = True
        elif not user_id:
            response = ('<html><body><h2>Invalid <i>API Key</i> '
                        '!</h2></body></html>')
        else:
            response = ("<html><body><h2>No <i>API Key</i> Provided "
                        "!</h2></body></html>")
        return response

    def generate_response(self, method, model, rec_id):
        """This function is used to generate the response based on the type
        of request and the parameters given"""
        option = request.env['connection.api'].search(
            [('model_id', '=', model)], limit=1)
        model_name = option.model_id.model
        if method != 'DELETE':
            data = json.loads(request.httprequest.data)
        else:
            data = {}
        fields = []
        if data:
            for field in data['fields']:
                fields.append(field)
        if not fields and method != 'DELETE':
            return ("<html><body><h2>No fields selected for the model"
                    "</h2></body></html>")
        if not option:
            return ("<html><body><h2>No Record Created for the model"
                    "</h2></body></html>")
        try:
            if method == 'GET':
                fields = []
                for field in data['fields']:
                    fields.append(field)
                if not option.is_get:
                    return ("<html><body><h2>Method Not Allowed"
                            "</h2></body></html>")
                else:
                    datas = []
                    if rec_id != 0:
                        partner_records = request.env[
                            str(model_name)].search_read(
                            domain=[('id', '=', rec_id)],
                            fields=fields
                        )
                        for record in partner_records:
                            for key, value in record.items():
                                if isinstance(value, (datetime, date)):
                                    record[key] = value.isoformat()
                        data = json.dumps({
                            'records': partner_records
                        })
                        datas.append(data)
                        return request.make_response(data=datas)
                    else:
                        partner_records = request.env[
                            str(model_name)].search_read(
                            domain=[],
                            fields=fields
                        )
                        for record in partner_records:
                            for key, value in record.items():
                                if isinstance(value, (datetime, date)):
                                    record[key] = value.isoformat()
                        data = json.dumps({
                            'records': partner_records
                        })
                        datas.append(data)
                        return request.make_response(data=datas)
        except:
            return ("<html><body><h2>Invalid JSON Data"
                    "</h2></body></html>")
        if method == 'POST':
            if not option.is_post:
                return ("<html><body><h2>Method Not Allowed"
                        "</h2></body></html>")
            else:
                try:
                    data = json.loads(request.httprequest.data)
                    datas = []
                    new_resource = request.env[str(model_name)].create(
                        data['values'])
                    partner_records = request.env[
                        str(model_name)].search_read(
                        domain=[('id', '=', new_resource.id)],
                        fields=fields
                    )
                    for record in partner_records:
                        for key, value in record.items():
                            if isinstance(value, (datetime, date)):
                                record[key] = value.isoformat()
                    new_data = json.dumps({'New resource': partner_records, })
                    datas.append(new_data)
                    return request.make_response(data=datas)
                except:
                    return ("<html><body><h2>Invalid JSON Data"
                            "</h2></body></html>")
        if method == 'PUT':
            if not option.is_put:
                return ("<html><body><h2>Method Not Allowed"
                        "</h2></body></html>")
            else:
                if rec_id == 0:
                    return ("<html><body><h2>No ID Provided"
                            "</h2></body></html>")
                else:
                    resource = request.env[str(model_name)].browse(
                        int(rec_id))
                    if not resource.exists():
                        return ("<html><body><h2>Resource not found"
                                "</h2></body></html>")
                    else:
                        try:
                            datas = []
                            data = json.loads(request.httprequest.data)
                            resource.write(data['values'])
                            partner_records = request.env[
                                str(model_name)].search_read(
                                domain=[('id', '=', resource.id)],
                                fields=fields
                            )
                            for record in partner_records:
                                for key, value in record.items():
                                    if isinstance(value, (datetime, date)):
                                        record[key] = value.isoformat()
                            new_data = json.dumps(
                                {'Updated resource': partner_records,
                                 })
                            datas.append(new_data)
                            return request.make_response(data=datas)

                        except:
                            return ("<html><body><h2>Invalid JSON Data "
                                    "!</h2></body></html>")
        if method == 'DELETE':
            if not option.is_delete:
                return ("<html><body><h2>Method Not Allowed"
                        "</h2></body></html>")
            else:
                if rec_id == 0:
                    return ("<html><body><h2>No ID Provided"
                            "</h2></body></html>")
                else:
                    resource = request.env[str(model_name)].browse(
                        int(rec_id))
                    if not resource.exists():
                        return ("<html><body><h2>Resource not found"
                                "</h2></body></html>")
                    else:

                        records = request.env[
                            str(model_name)].search_read(
                            domain=[('id', '=', resource.id)],
                            fields=['id', 'display_name']
                        )
                        remove = json.dumps(
                            {"Resource deleted": records,
                             })
                        resource.unlink()
                        return request.make_response(data=remove)

    @http.route(['/send_request'], type='http',
                auth='none',
                methods=['GET', 'POST', 'PUT', 'DELETE'], csrf=False)
    def fetch_data(self, **kw):
        """This controller will be called when sending a request to the
        specified url, and it will authenticate the api-key and then will
        generate the result"""
        http_method = request.httprequest.method

        api_key = request.httprequest.headers.get('api-key')
        auth_api = self.auth_api_key(api_key)
        model = kw.get('model')
        username = request.httprequest.headers.get('login')
        password = request.httprequest.headers.get('password')
        credential = {'login': username, 'password': password, 'type': 'password'}
        request.session.authenticate(request.session.db, credential)
        model_id = request.env['ir.model'].search(
            [('model', '=', model)])
        if not model_id:
            return ("<html><body><h3>Invalid model, check spelling or maybe "
                    "the related "
                    "module is not installed"
                    "</h3></body></html>")

        if auth_api == True:
            if not kw.get('Id'):
                rec_id = 0
            else:
                rec_id = int(kw.get('Id'))
            result = self.generate_response(http_method, model_id.id, rec_id)
            return result
        else:
            return auth_api

    @http.route(['/odoo_connect', '/odoo_connect/'], type="http", auth="none", csrf=False,
                methods=['GET'])
    def odoo_connect(self, **kw):
        """This is the controller which initializes the api transaction by
        generating the api-key for specific user and database"""
        username = request.httprequest.headers.get('login')
        password = request.httprequest.headers.get('password')
        db = request.httprequest.headers.get('db')
        try:
            request.session.update(http.get_default_session(), db=db)
            credential = {'login': username, 'password': password,
                          'type': 'password'}

            auth = request.session.authenticate(db, credential)
            user = request.env['res.users'].browse(auth['uid'])
            api_key = request.env.user.generate_api(username)
            datas = json.dumps({"Status": "auth successful",
                                "User": user.name,
                                "api-key": api_key})
            return request.make_response(data=datas)
        except:
            return ("<html><body><h2>wrong login credentials"
                    "</h2></body></html>")

    @http.route(['/loan_leads'], type='http',
                auth='none',
                methods=['POST'], csrf=False)
    def create_loan_lead(self, **kw):
        """Dedicated endpoint for creating loan leads with flat payload structure.
        Uses API key authentication from rest_api_odoo.
        """
        import json
        
        # Authenticate using API key and get user
        api_key = request.httprequest.headers.get('api-key')
        if not api_key:
            return ("<html><body><h2>No <i>API Key</i> Provided</h2></body></html>")
        
        # Get database name from headers or session
        db = request.httprequest.headers.get('db') or request.session.db
        if not db:
            # Try to get from request context
            db = getattr(request, 'db', None)
        if not db:
            return ("<html><body><h2>Database not specified. Please provide 'db' header.</h2></body></html>")
        
        # Initialize session with database
        try:
            request.session.update(http.get_default_session(), db=db)
        except Exception:
            pass
        
        # Get user from API key
        user = request.env['res.users'].sudo().search([('api_key', '=', api_key)], limit=1)
        if not user:
            return ("<html><body><h2>Invalid <i>API Key</i>!</h2></body></html>")
        
        # Set up environment with authenticated user
        env = request.env(user=user.id)
        
        # Get payload
        try:
            payload = json.loads(request.httprequest.data)
        except Exception as e:
            _logger.error("Error parsing JSON: %s", str(e))
            return ("<html><body><h2>Invalid JSON Data</h2></body></html>")
        
        # Helper functions
        def _get(key, default=None):
            return payload.get(key, default)
        
        def _float(val):
            try:
                return float(val) if val else 0.0
            except (ValueError, TypeError):
                return 0.0
        
        def _int(val):
            try:
                if isinstance(val, str):
                    digits = "".join(ch for ch in val if ch.isdigit())
                    return int(digits) if digits else 0
                return int(val) if val else 0
            except (ValueError, TypeError):
                return 0
        
        def _clean_vals(vals_dict):
            """Remove None and empty string values from dict, but keep False for Many2one fields"""
            cleaned = {}
            for k, v in vals_dict.items():
                if v is False:
                    cleaned[k] = v
                elif v is not None and v != "":
                    cleaned[k] = v
            return cleaned
        
        # Normalize customer_type
        ctype_raw = (_get("customer_type") or "").lower().strip()
        ctype_map = {
            "consumer": "individual",
            "corporate": "company",
            "cooperate": "company",
            "individual": "individual",
            "company": "company",
        }
        ctype = ctype_map.get(ctype_raw)
        
        # Collect document URLs from flat payload
        doc_urls = {
            "loan_documents": [],
            "passport": [],
            "govt_issued_id": [],
            "staff_id": [],
            "pay_slip": [],
            "bank_statement": [],
            "utility_bill": [],
            "certificate_of_incorporation": [],
        }
        
        for key, value in payload.items():
            if value and isinstance(value, str):
                if key.startswith("loan_documents_"):
                    doc_urls["loan_documents"].append(value)
                elif key == "kyc_documents_passport":
                    doc_urls["passport"].append(value)
                elif key == "kyc_documents_govt_issued_id":
                    doc_urls["govt_issued_id"].append(value)
                elif key == "kyc_documents_staff_id":
                    doc_urls["staff_id"].append(value)
                elif key == "kyc_documents_pay_slip":
                    doc_urls["pay_slip"].append(value)
                elif key == "kyc_documents_bank_statement":
                    doc_urls["bank_statement"].append(value)
                elif key == "kyc_documents_utility_bill":
                    doc_urls["utility_bill"].append(value)
                elif key == "kyc_documents_certificate_of_incorporation":
                    doc_urls["certificate_of_incorporation"].append(value)
        
        # Base values
        vals = {
            "type": "lead",
            "user_id": int(_get("user_id")) if _get("user_id") else False,
            "loan_amount": _float(_get("loan_amount") or _get("amount")),
            "loan_term": _int(_get("loan_term") or _get("tenor")),
            "loan_purpose": _get("loan_purpose") or _get("purpose"),
            "collateral": _get("collateral"),
            "source_of_repayment": _get("source_of_repayment"),
            "customer_type": ctype,
            "external_reference": _get("reference"),
            "external_status": _get("status"),
            "external_kyc_id": str(_get("kyc_id")) if _get("kyc_id") is not None else False,
            # Document URLs (first link per type)
            "loan_document_url": doc_urls["loan_documents"][0] if doc_urls["loan_documents"] else False,
            "passport_url": doc_urls["passport"][0] if doc_urls["passport"] else False,
            "govt_issued_id_url": doc_urls["govt_issued_id"][0] if doc_urls["govt_issued_id"] else False,
            "staff_id_url": doc_urls["staff_id"][0] if doc_urls["staff_id"] else False,
            "pay_slip_url": doc_urls["pay_slip"][0] if doc_urls["pay_slip"] else False,
            "bank_statement_url": doc_urls["bank_statement"][0] if doc_urls["bank_statement"] else False,
            "utility_bill_url": doc_urls["utility_bill"][0] if doc_urls["utility_bill"] else False,
            "certificate_of_incorporation_url": doc_urls["certificate_of_incorporation"][0] if doc_urls["certificate_of_incorporation"] else False,
            # Preserve all URLs as JSON strings
            "loan_document_urls": json.dumps(doc_urls["loan_documents"]),
            "passport_urls": json.dumps(doc_urls["passport"]),
            "govt_issued_id_urls": json.dumps(doc_urls["govt_issued_id"]),
            "staff_id_urls": json.dumps(doc_urls["staff_id"]),
            "pay_slip_urls": json.dumps(doc_urls["pay_slip"]),
            "bank_statement_urls": json.dumps(doc_urls["bank_statement"]),
            "utility_bill_urls": json.dumps(doc_urls["utility_bill"]),
            "certificate_of_incorporation_urls": json.dumps(doc_urls["certificate_of_incorporation"]),
        }
        
        if not ctype:
            vals.pop("customer_type", None)
        
        # Handle loan_type_id
        if _get("loan_type_id") is not None:
            try:
                vals["loan_type_id"] = int(_get("loan_type_id"))
            except Exception:
                return ("<html><body><h2>Invalid loan_type_id</h2></body></html>")
        
        # Corporate vs Individual mapping
        if ctype == "company":
            comp_name = _get("company_name") or _get("reference") or "Company"
            corp_vals = {
                "name": comp_name,
                "partner_name": comp_name,
                "company_name": _get("company_name"),
                "company_email": _get("company_email"),
                "company_phone": _get("company_phone"),
                "company_address": _get("company_address"),
                "company_rc_number": _get("company_rc_number") or _get("rc_number"),
                "date_of_incorporation": _get("date_of_incorporation"),
                "annual_turnover": _float(_get("annual_turnover")),
                "director_title": _get("director_title"),
                "director_name": " ".join(filter(None, [
                    _get("director_first_name"),
                    _get("director_middle_name"),
                    _get("director_surname")
                ])) or False,
                "director_phone": _get("director_phone"),
                "director_email": _get("director_email"),
                "director_nin": _get("director_nin"),
                "director_bvn": _get("director_bvn"),
                "director_date_of_birth": _get("director_date_of_birth") or _get("director_dob"),
                "director_address": _get("director_address"),
                "director_marital_status": _get("director_marital_status"),
                "director_designation": _get("director_designation"),
            }
            vals.update(_clean_vals(corp_vals))
        else:
            full_name = " ".join(filter(None, [
                _get("applicant_first_name"),
                _get("applicant_middle_name"),
                _get("applicant_surname")
            ])) or _get("reference") or "Lead"
            indiv_vals = {
                "name": full_name,
                "contact_name": full_name,
                "email_from": _get("applicant_email"),
                "phone": _get("applicant_phone"),
                "nin": _get("applicant_nin"),
                "bvn": _get("applicant_bvn"),
                "marital_status": _get("applicant_marital_status"),
                "applicant_title": _get("applicant_title"),
                "applicant_address": _get("applicant_address"),
                "nok_name": _get("next_of_kin_name"),
                "nok_phone": _get("next_of_kin_phone"),
                "nok_address": _get("next_of_kin_address"),
                "nok_relationship": _get("next_of_kin_relationship"),
                "nok_occupation": _get("next_of_kin_occupation"),
                "nok_email": _get("next_of_kin_email"),
                "company_name": _get("employment_company_name"),
                "company_email": _get("employment_company_email"),
                "company_address": _get("employment_company_address"),
                "salary": _float(_get("employment_salary")),
                "service_length": _int(_get("employment_length_of_service")),
                "designation": _get("employment_designation"),
            }
            vals.update(_clean_vals(indiv_vals))
        
        vals["name"] = vals.get("name") or _get("reference") or "Lead"
        
        # Guarantor fields
        guar_vals = {
            "guarantor_title": _get("guarantor_title"),
            "guarantor_name": _get("guarantor_name"),
            "guarantor_phone": _get("guarantor_phone"),
            "guarantor_email": _get("guarantor_email"),
            "guarantor_relationship": _get("guarantor_relationship"),
        }
        vals.update(_clean_vals(guar_vals))
        
        vals = _clean_vals(vals)
        
        # Create partner
        partner_id = False
        if ctype == "company":
            partner_name = _get("company_name") or _get("reference") or "Company"
            partner = env["res.partner"].sudo().search([
                ("name", "=", partner_name),
                ("is_company", "=", True)
            ], limit=1)
            if not partner and partner_name:
                partner = env["res.partner"].sudo().create({
                    "name": partner_name,
                    "is_company": True,
                    "email": _get("company_email"),
                    "phone": _get("company_phone"),
                    "street": _get("company_address"),
                })
            partner_id = partner.id if partner else False
        else:
            email = _get("applicant_email")
            phone = _get("applicant_phone")
            partner = False
            if email:
                partner = env["res.partner"].sudo().search([
                    ("email", "=", email),
                    ("is_company", "=", False)
                ], limit=1)
            if not partner and phone:
                partner = env["res.partner"].sudo().search([
                    ("phone", "=", phone),
                    ("is_company", "=", False)
                ], limit=1)
            if not partner:
                full_name = vals.get("name") or _get("reference") or "Lead"
                partner = env["res.partner"].sudo().create({
                    "name": full_name,
                    "is_company": False,
                    "email": email,
                    "phone": phone,
                    "street": _get("applicant_address"),
                })
            partner_id = partner.id if partner else False
        
        if partner_id:
            vals["partner_id"] = partner_id
        
        # Create lead
        try:
            lead = env["crm.lead"].sudo().create(vals)
            if not lead.partner_id and partner_id:
                lead.sudo().write({"partner_id": partner_id})
            
            result = json.dumps({
                "id": lead.id,
                "partner_id": lead.partner_id.id if lead.partner_id else partner_id,
                "customer_type": lead.customer_type,
            })
            return request.make_response(data=result, headers=[('Content-Type', 'application/json')])
        except Exception as e:
            _logger.error("Error creating loan lead: %s", str(e), exc_info=True)
            return ("<html><body><h2>Error creating lead: %s</h2><p>Check Odoo logs for details.</p></body></html>" % str(e))

    @http.route(['/loan_requests'], type='http',
                auth='none',
                methods=['POST'], csrf=False)
    def create_loan_request(self, **kw):
        """Dedicated endpoint for creating loan requests directly with flat payload structure.
        Uses API key authentication from rest_api_odoo.
        Creates dev.loan.loan records directly (bypassing CRM leads).
        """
        import json
        
        # Authenticate using API key and get user
        api_key = request.httprequest.headers.get('api-key')
        if not api_key:
            return ("<html><body><h2>No <i>API Key</i> Provided</h2></body></html>")
        
        # Get database name from headers or session
        db = request.httprequest.headers.get('db') or request.session.db
        if not db:
            db = getattr(request, 'db', None)
        if not db:
            return ("<html><body><h2>Database not specified. Please provide 'db' header.</h2></body></html>")
        
        # Initialize session with database
        try:
            request.session.update(http.get_default_session(), db=db)
        except Exception:
            pass
        
        # Get user from API key
        user = request.env['res.users'].sudo().search([('api_key', '=', api_key)], limit=1)
        if not user:
            return ("<html><body><h2>Invalid <i>API Key</i>!</h2></body></html>")
        
        # Set up environment with authenticated user
        env = request.env(user=user.id)
        
        # Get payload
        try:
            payload = json.loads(request.httprequest.data)
        except Exception as e:
            _logger.error("Error parsing JSON: %s", str(e))
            return ("<html><body><h2>Invalid JSON Data</h2></body></html>")
        
        # Helper functions
        def _get(key, default=None):
            return payload.get(key, default)
        
        def _float(val):
            try:
                return float(val) if val else 0.0
            except (ValueError, TypeError):
                return 0.0
        
        def _int(val):
            try:
                if isinstance(val, str):
                    digits = "".join(ch for ch in val if ch.isdigit())
                    return int(digits) if digits else 0
                return int(val) if val else 0
            except (ValueError, TypeError):
                return 0
        
        def _clean_vals(vals_dict):
            """Remove None and empty string values from dict, but keep False for Many2one fields"""
            cleaned = {}
            for k, v in vals_dict.items():
                if v is False:
                    cleaned[k] = v
                elif v is not None and v != "":
                    cleaned[k] = v
            return cleaned
        
        # Normalize customer_type
        ctype_raw = (_get("customer_type") or "").lower().strip()
        ctype_map = {
            "consumer": "individual",
            "corporate": "company",
            "cooperate": "company",
            "individual": "individual",
            "company": "company",
        }
        ctype = ctype_map.get(ctype_raw)
        
        # Collect document URLs from flat payload
        doc_urls = {
            "loan_documents": [],
            "passport": [],
            "govt_issued_id": [],
            "staff_id": [],
            "pay_slip": [],
            "bank_statement": [],
            "utility_bill": [],
            "certificate_of_incorporation": [],
        }
        
        for key, value in payload.items():
            if key.startswith("loan_documents_"):
                if value:
                    doc_urls["loan_documents"].append(value)
            elif key.startswith("kyc_documents_passport"):
                if value:
                    doc_urls["passport"].append(value)
            elif key.startswith("kyc_documents_govt_issued_id"):
                if value:
                    doc_urls["govt_issued_id"].append(value)
            elif key.startswith("kyc_documents_staff_id"):
                if value:
                    doc_urls["staff_id"].append(value)
            elif key.startswith("kyc_documents_pay_slip"):
                if value:
                    doc_urls["pay_slip"].append(value)
            elif key.startswith("kyc_documents_bank_statement"):
                if value:
                    doc_urls["bank_statement"].append(value)
            elif key.startswith("kyc_documents_utility_bill"):
                if value:
                    doc_urls["utility_bill"].append(value)
            elif key.startswith("kyc_documents_certificate_of_incorporation"):
                if value:
                    doc_urls["certificate_of_incorporation"].append(value)
        
        # Base loan values
        vals = {
            "state": "draft",
            "user_id": int(_get("user_id")) if _get("user_id") else user.id,
            "loan_amount": _float(_get("loan_amount") or _get("amount")),
            "loan_term": _int(_get("loan_term") or _get("tenor")),
            "loan_purpose": _get("loan_purpose") or _get("purpose"),
            "collateral": _get("collateral"),
            "source_of_repayment": _get("source_of_repayment"),
            "customer_type": ctype or "individual",
            # External metadata
            "external_reference": _get("reference"),
            "external_status": _get("status"),
            "external_kyc_id": str(_get("kyc_id")) if _get("kyc_id") is not None else False,
            # Document URL fields (first link per type)
            "loan_document_url": doc_urls["loan_documents"][0] if doc_urls["loan_documents"] else False,
            "passport_url": doc_urls["passport"][0] if doc_urls["passport"] else False,
            "govt_issued_id_url": doc_urls["govt_issued_id"][0] if doc_urls["govt_issued_id"] else False,
            "staff_id_url": doc_urls["staff_id"][0] if doc_urls["staff_id"] else False,
            "pay_slip_url": doc_urls["pay_slip"][0] if doc_urls["pay_slip"] else False,
            "bank_statement_url": doc_urls["bank_statement"][0] if doc_urls["bank_statement"] else False,
            "utility_bill_url": doc_urls["utility_bill"][0] if doc_urls["utility_bill"] else False,
            "certificate_of_incorporation_url": doc_urls["certificate_of_incorporation"][0] if doc_urls["certificate_of_incorporation"] else False,
            # Preserve all URLs as JSON strings
            "loan_document_urls": json.dumps(doc_urls["loan_documents"]),
            "passport_urls": json.dumps(doc_urls["passport"]),
            "govt_issued_id_urls": json.dumps(doc_urls["govt_issued_id"]),
            "staff_id_urls": json.dumps(doc_urls["staff_id"]),
            "pay_slip_urls": json.dumps(doc_urls["pay_slip"]),
            "bank_statement_urls": json.dumps(doc_urls["bank_statement"]),
            "utility_bill_urls": json.dumps(doc_urls["utility_bill"]),
            "certificate_of_incorporation_urls": json.dumps(doc_urls["certificate_of_incorporation"]),
        }
        
        # Handle loan_type_id (required for loan)
        if _get("loan_type_id") is not None:
            try:
                vals["loan_type_id"] = int(_get("loan_type_id"))
            except Exception:
                return ("<html><body><h2>Invalid loan_type_id</h2></body></html>")
        else:
            return ("<html><body><h2>loan_type_id is required</h2></body></html>")
        
        # Corporate vs Individual mapping
        if ctype == "company":
            comp_name = _get("company_name") or _get("reference") or "Company"
            corp_vals = {
                "company_phone": _get("company_phone"),
                "date_of_incorporation": _get("date_of_incorporation"),
                "annual_turnover": _float(_get("annual_turnover")),
                "company_rc_number": _get("company_rc_number") or _get("rc_number"),
                "company_bank_name": _get("company_bank_name"),
                "company_bank_account_number": _get("company_bank_account_number"),
                "company_bank_account_name": _get("company_bank_account_name"),
                "director_title": _get("director_title"),
                "director_name": " ".join(filter(None, [
                    _get("director_first_name"),
                    _get("director_middle_name"),
                    _get("director_surname")
                ])) or False,
                "director_phone": _get("director_phone"),
                "director_email": _get("director_email"),
                "director_nin": _get("director_nin"),
                "director_bvn": _get("director_bvn"),
                "director_date_of_birth": _get("director_date_of_birth") or _get("director_dob"),
                "director_address": _get("director_address"),
                "director_marital_status": _get("director_marital_status"),
                "director_designation": _get("director_designation"),
            }
            vals.update(_clean_vals(corp_vals))
        else:
            indiv_vals = {
                "bvn": _get("applicant_bvn") or _get("bvn"),
                "nin": _get("applicant_nin") or _get("nin"),
                "marital_status": _get("applicant_marital_status") or _get("marital_status"),
                "applicant_title": _get("applicant_title"),
                "applicant_address": _get("applicant_address"),
                "bank_name": _get("bank_name"),
                "account_number": _get("account_number"),
                "nok_name": _get("next_of_kin_name"),
                "nok_phone": _get("next_of_kin_phone"),
                "nok_address": _get("next_of_kin_address"),
                "nok_relationship": _get("next_of_kin_relationship"),
                "nok_occupation": _get("next_of_kin_occupation"),
                "nok_email": _get("next_of_kin_email"),
                "employment_company_name": _get("employment_company_name"),
                "employment_company_email": _get("employment_company_email"),
                "employment_company_address": _get("employment_company_address"),
                "salary": _float(_get("employment_salary")),
                "service_length": _int(_get("employment_length_of_service")),
                "designation": _get("employment_designation"),
            }
            vals.update(_clean_vals(indiv_vals))
        
        # Guarantor fields
        guar_vals = {
            "guarantor_title": _get("guarantor_title"),
            "guarantor_name": _get("guarantor_name"),
            "guarantor_phone": _get("guarantor_phone"),
            "guarantor_email": _get("guarantor_email"),
            "guarantor_relationship": _get("guarantor_relationship"),
        }
        vals.update(_clean_vals(guar_vals))
        
        vals = _clean_vals(vals)
        
        # Create partner
        partner_id = False
        if ctype == "company":
            partner_name = _get("company_name") or _get("reference") or "Company"
            partner = env["res.partner"].sudo().search([
                ("name", "=", partner_name),
                ("is_company", "=", True)
            ], limit=1)
            if not partner and partner_name:
                partner = env["res.partner"].sudo().create({
                    "name": partner_name,
                    "is_company": True,
                    "email": _get("company_email"),
                    "phone": _get("company_phone"),
                    "street": _get("company_address"),
                    "is_allow_loan": True,
                })
            partner_id = partner.id if partner else False
        else:
            email = _get("applicant_email")
            phone = _get("applicant_phone")
            bvn = _get("applicant_bvn") or _get("bvn")
            nin = _get("applicant_nin") or _get("nin")
            partner = False
            
            # Priority 1: Match by Email
            if email:
                partner = env["res.partner"].sudo().search([
                    ("email", "=", email),
                    ("is_company", "=", False)
                ], limit=1)
            
            # Priority 2: Match by Phone (if email didn't match)
            if not partner and phone:
                partner = env["res.partner"].sudo().search([
                    ("phone", "=", phone),
                    ("is_company", "=", False)
                ], limit=1)
            
            # Priority 3: Match by BVN (if email and phone didn't match)
            if not partner and bvn:
                partner = env["res.partner"].sudo().search([
                    ("bvn", "=", bvn),
                    ("is_company", "=", False)
                ], limit=1)
            
            # Priority 4: Match by NIN (if email, phone, and BVN didn't match)
            if not partner and nin:
                partner = env["res.partner"].sudo().search([
                    ("nin", "=", nin),
                    ("is_company", "=", False)
                ], limit=1)
            
            # Only create new partner if no match found

            # Get borrower_category_id from request or use default
            borrower_category_id = _get("borrower_category_id")
            if not borrower_category_id:
                # Get default category
                default_category = env["borrower.category"].sudo().search([
                    ("is_default", "=", True)
                ], limit=1)
                if default_category:
                    borrower_category_id = default_category.id
            
            # Only create new partner if no match found
            if not partner:
                full_name = " ".join(filter(None, [
                    _get("applicant_first_name"),
                    _get("applicant_middle_name"),
                    _get("applicant_surname")
                ])) or _get("reference") or "Customer"
                
                partner_vals = {
                    "name": full_name,
                    "is_company": False,
                    "email": email,
                    "phone": phone,
                    "street": _get("applicant_address"),
                    "bvn": bvn,
                    "nin": nin,
                    "is_allow_loan": True,
                }
                
                # Set borrower_category_id if provided or default exists
                if borrower_category_id:
                    partner_vals["borrower_category_id"] = int(borrower_category_id)
                    # loan_request will be automatically set by the create method
                
                partner = env["res.partner"].sudo().create(partner_vals)
            else:
                # Update partner details if new information is provided
                update_vals = {}
                full_name = " ".join(filter(None, [
                    _get("applicant_first_name"),
                    _get("applicant_middle_name"),
                    _get("applicant_surname")
                ]))
                if full_name and partner.name != full_name:
                    update_vals["name"] = full_name
                if email and partner.email != email:
                    update_vals["email"] = email
                if phone and partner.phone != phone:
                    update_vals["phone"] = phone
                if bvn and not partner.bvn:
                    update_vals["bvn"] = bvn
                if nin and not partner.nin:
                    update_vals["nin"] = nin
                if _get("applicant_address") and partner.street != _get("applicant_address"):
                    update_vals["street"] = _get("applicant_address")
                
                # Update borrower_category_id if provided
                if borrower_category_id:
                    update_vals["borrower_category_id"] = int(borrower_category_id)
                    # loan_request will be automatically set by the write method
                
                if update_vals:
                    partner.sudo().write(update_vals)
            
            partner_id = partner.id if partner else False
        
        if partner_id:
            vals["client_id"] = partner_id
        
        # Create loan request
        try:
            loan = env["dev.loan.loan"].sudo().create(vals)
            # Trigger onchange to set defaults from loan type
            loan.onchange_loan_type()
            
            result = json.dumps({
                "id": loan.id,
                "name": loan.name,
                "client_id": loan.client_id.id if loan.client_id else partner_id,
                "customer_type": loan.customer_type,
                "state": loan.state,
            })
            return request.make_response(data=result, headers=[('Content-Type', 'application/json')])
        except Exception as e:
            _logger.error("Error creating loan request: %s", str(e), exc_info=True)
            return ("<html><body><h2>Error creating loan request: %s</h2><p>Check Odoo logs for details.</p></body></html>" % str(e))
    @http.route(['/loans'], type='http', auth='none', methods=['GET'], csrf=False)
    def get_all_loans(self, **kw):
        """Return all loans with optional fields filter via query param:
        ?fields=id,name,state,loan_amount"""
        api_key = request.httprequest.headers.get('api-key')
        if not api_key:
            return ("<html><body><h2>No <i>API Key</i> Provided</h2></body></html>")
        # Resolve DB from headers or session
        db = request.httprequest.headers.get('db') or request.session.db
        if not db:
            db = getattr(request, 'db', None)
        if not db:
            return ("<html><body><h2>Database not specified. Please provide 'db' header.</h2></body></html>")
        try:
            request.session.update(http.get_default_session(), db=db)
        except Exception:
            pass
        # Authenticate user by API key
        user = request.env['res.users'].sudo().search([('api_key', '=', api_key)], limit=1)
        if not user:
            return ("<html><body><h2>Invalid <i>API Key</i>!</h2></body></html>")
        env = request.env(user=user.id)
        # Fields handling
        default_fields = ['id', 'name', 'state', 'client_id', 'loan_amount', 'loan_type_id', 'request_date', 'approve_date', 'disbursement_date']
        fields_param = kw.get('fields')
        fields = [f.strip() for f in fields_param.split(',')] if fields_param else default_fields
        try:
            records = env['dev.loan.loan'].sudo().search_read(domain=[], fields=fields)
            # Convert date/datetime to isoformat
            for rec in records:
                for k, v in rec.items():
                    if isinstance(v, (datetime, date)):
                        rec[k] = v.isoformat()
            payload = json.dumps({'records': records})
            return request.make_response(data=payload, headers=[('Content-Type', 'application/json')])
        except Exception as e:
            _logger.error("Error fetching loans: %s", str(e), exc_info=True)
            return ("<html><body><h2>Error fetching loans</h2></body></html>")

    @http.route(['/loans/<int:loan_id>/stage'], type='http', auth='none', methods=['GET'], csrf=False)
    def get_loan_stage(self, loan_id, **kw):
        """Return the current stage (state) of a loan by ID."""
        api_key = request.httprequest.headers.get('api-key')
        if not api_key:
            return ("<html><body><h2>No <i>API Key</i> Provided</h2></body></html>")
        # Resolve DB
        db = request.httprequest.headers.get('db') or request.session.db
        if not db:
            db = getattr(request, 'db', None)
        if not db:
            return ("<html><body><h2>Database not specified. Please provide 'db' header.</h2></body></html>")
        try:
            request.session.update(http.get_default_session(), db=db)
        except Exception:
            pass
        # Authenticate user
        user = request.env['res.users'].sudo().search([('api_key', '=', api_key)], limit=1)
        if not user:
            return ("<html><body><h2>Invalid <i>API Key</i>!</h2></body></html>")
        env = request.env(user=user.id)
        try:
            loan = env['dev.loan.loan'].sudo().browse(loan_id)
            if not loan.exists():
                return ("<html><body><h2>Loan not found</h2></body></html>")
            payload = json.dumps({'id': loan.id, 'state': loan.state})
            return request.make_response(data=payload, headers=[('Content-Type', 'application/json')])
        except Exception as e:
            _logger.error("Error fetching loan stage: %s", str(e), exc_info=True)
            return ("<html><body><h2>Error fetching loan stage</h2></body></html>")

    @http.route(['/wallet/create-tier-one'], type='http', auth='none', methods=['POST'], csrf=False)
    def create_wallet_tier_one(self, **kw):
        """Create Tier One wallet with BVN using BaaS API
        
        Required headers:
        - api-key: API key for authentication
        - db: Database name
        - Content-Type: application/json
        
        Request body (JSON):
        {
            "bvn": "31035529413",
            "firstname": "John",
            "lastname": "Doe",
            "phone": "3103452948",
            "dob": "1990-01-15",
            "partner_id": 123  // Optional
        }
        
        Returns JSON response with success status and account number
        """
        import json
        
        # Authenticate using API key
        api_key = request.httprequest.headers.get('api-key')
        if not api_key:
            error_response = {
                "success": False,
                "message": "No API Key provided",
                "account_number": None,
                "errors": ["Missing api-key header"]
            }
            return request.make_response(
                data=json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=401
            )
        
        # Get database name from headers or session
        db = request.httprequest.headers.get('db') or request.session.db
        if not db:
            db = getattr(request, 'db', None)
        if not db:
            error_response = {
                "success": False,
                "message": "Database not specified",
                "account_number": None,
                "errors": ["Missing db header"]
            }
            return request.make_response(
                data=json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=400
            )
        
        # Initialize session with database
        try:
            request.session.update(http.get_default_session(), db=db)
        except Exception as e:
            _logger.warning("Session update failed: %s", str(e))
        
        # Get user from API key
        user = request.env['res.users'].sudo().search([('api_key', '=', api_key)], limit=1)
        if not user:
            error_response = {
                "success": False,
                "message": "Invalid API Key",
                "account_number": None,
                "errors": ["Invalid or expired api-key"]
            }
            return request.make_response(
                data=json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=401
            )
        
        # Set up environment with authenticated user
        env = request.env(user=user.id)
        
        # Get and parse payload
        try:
            payload_data = request.httprequest.data
            if not payload_data:
                error_response = {
                    "success": False,
                    "message": "Empty request body",
                    "account_number": None,
                    "errors": ["Request body is required"]
                }
                return request.make_response(
                    data=json.dumps(error_response),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            payload = json.loads(payload_data)
        except json.JSONDecodeError as e:
            _logger.error("Error parsing JSON: %s", str(e))
            error_response = {
                "success": False,
                "message": "Invalid JSON data",
                "account_number": None,
                "errors": [f"JSON decode error: {str(e)}"]
            }
            return request.make_response(
                data=json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=400
            )
        except Exception as e:
            _logger.error("Error reading request data: %s", str(e))
            error_response = {
                "success": False,
                "message": "Error reading request data",
                "account_number": None,
                "errors": [str(e)]
            }
            return request.make_response(
                data=json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=400
            )
        
        # Helper to get value with fallback
        def _get(key, default=None):
            return payload.get(key, default)
        
        # Validate required fields
        bvn = _get("bvn") or _get("bvn_number")
        firstname = _get("firstname") or _get("first_name")
        lastname = _get("lastname") or _get("last_name")
        phone = _get("phone") or _get("phone_number")
        dob = _get("dob") or _get("date_of_birth") or _get("birthdate")
        partner_id = _get("partner_id")
        
        # Validate required fields
        missing_fields = []
        if not bvn:
            missing_fields.append("bvn")
        if not firstname:
            missing_fields.append("firstname")
        if not lastname:
            missing_fields.append("lastname")
        if not phone:
            missing_fields.append("phone")
        if not dob:
            missing_fields.append("dob")
        
        if missing_fields:
            error_response = {
                "success": False,
                "message": f"Missing required fields: {', '.join(missing_fields)}",
                "account_number": None,
                "errors": [f"Required fields: {', '.join(missing_fields)}"]
            }
            return request.make_response(
                data=json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=400
            )
        
        # If partner_id provided, use it; otherwise create wallet directly
        if partner_id:
            try:
                partner_id_int = int(partner_id)
                partner = env['res.partner'].sudo().browse(partner_id_int)
                if not partner.exists():
                    error_response = {
                        "success": False,
                        "message": "Partner not found",
                        "account_number": None,
                        "errors": [f"Partner with ID {partner_id} does not exist"]
                    }
                    return request.make_response(
                        data=json.dumps(error_response),
                        headers=[('Content-Type', 'application/json')],
                        status=404
                    )
                result = partner.create_wallet_tier_one(bvn=bvn)
            except ValueError:
                error_response = {
                    "success": False,
                    "message": "Invalid partner_id format",
                    "account_number": None,
                    "errors": ["partner_id must be a valid integer"]
                }
                return request.make_response(
                    data=json.dumps(error_response),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            except ValidationError as e:
                _logger.error("Validation error creating wallet for partner: %s", str(e))
                error_response = {
                    "success": False,
                    "message": str(e),
                    "account_number": None,
                    "errors": [str(e)]
                }
                return request.make_response(
                    data=json.dumps(error_response),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            except Exception as e:
                _logger.error("Error creating wallet for partner: %s", str(e), exc_info=True)
                error_response = {
                    "success": False,
                    "message": "Error creating wallet",
                    "account_number": None,
                    "errors": [f"Internal error: {str(e)}"]
                }
                return request.make_response(
                    data=json.dumps(error_response),
                    headers=[('Content-Type', 'application/json')],
                    status=500
                )
        else:
            # Create wallet directly via service
            try:
                baas_service = env['baas.service']
                result = baas_service.create_tier_one_wallet(
                    firstname=firstname,
                    lastname=lastname,
                    phone=phone,
                    dob=dob,
                    bvn=bvn
                )
            except ValidationError as e:
                _logger.error("Validation error creating wallet: %s", str(e))
                error_response = {
                    "success": False,
                    "message": str(e),
                    "account_number": None,
                    "errors": [str(e)]
                }
                return request.make_response(
                    data=json.dumps(error_response),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            except Exception as e:
                _logger.error("Error creating wallet via service: %s", str(e), exc_info=True)
                error_response = {
                    "success": False,
                    "message": "Error creating wallet",
                    "account_number": None,
                    "errors": [f"Internal error: {str(e)}"]
                }
                return request.make_response(
                    data=json.dumps(error_response),
                    headers=[('Content-Type', 'application/json')],
                    status=500
                )
        
        # Return response
        status_code = 200 if result.get('success') else 400
        response_data = {
            "success": result.get('success', False),
            "account_number": result.get('account_number'),
            "message": result.get('message', ''),
            "wallet_tier": "tier_1",
            "errors": result.get('errors', [])
        }
        
        return request.make_response(
            data=json.dumps(response_data),
            headers=[('Content-Type', 'application/json')],
            status=status_code
        )