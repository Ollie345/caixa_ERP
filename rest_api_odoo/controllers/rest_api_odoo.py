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

    @http.route(['/odoo_connect'], type="http", auth="none", csrf=False,
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
