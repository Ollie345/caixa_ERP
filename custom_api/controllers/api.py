# -*- coding: utf-8 -*-
import json
import logging
from werkzeug.exceptions import BadRequest, Unauthorized
from odoo import http
from odoo.http import request

# Import key crypt context from base to validate api-keys
try:
    from odoo.addons.base.models.res_users import KEY_CRYPT_CONTEXT, INDEX_SIZE
except Exception:
    KEY_CRYPT_CONTEXT = None
    INDEX_SIZE = 8

API_PREFIX = "/custom/api/v1"


# Whitelist of loan-related lead fields accepted from the API
LOAN_LEAD_FIELDS = [
    # Loan Details
    "loan_type_id", "loan_amount", "loan_term", "collateral",
    "source_of_repayment", "loan_purpose",
    # Other Application Details
    "bvn", "nin", "bank_name", "account_number", "marital_status", "partner_tin",
    # Next of Kin Details
    "nok_name", "nok_phone", "nok_address", "nok_relationship", "nok_occupation", "nok_email",
    # Employment Details
    "company_name", "company_address", "company_email", "salary", "service_length", "designation",
    # Guarantor Details
    "guarantor_name", "guarantor_phone", "guarantor_email", "guarantor_relationship",
    # Corporate Company Info
    "company_phone", "date_of_incorporation", "annual_turnover", "company_rc_number",
    "company_bank_name", "company_bank_account_number", "company_bank_account_name",
    # Director Information
    "director_name", "director_phone", "director_email", "director_nin",
    "director_date_of_birth", "director_bvn", "director_address", "director_marital_status",
    "director_designation",
]


def _get_api_key(env, token):
    """Return the api‐key record for *token* or False."""
    # CE 17+/18: res.users.apikeys table (custom SQL because 'key' isn't an ORM field)
    if KEY_CRYPT_CONTEXT and "res.users.apikeys" in env:
        index = token[:INDEX_SIZE]
        env.cr.execute(
            """
            SELECT id, user_id, key
            FROM res_users_apikeys
            WHERE index = %s
            """,
            [index],
        )
        for api_id, user_id, stored_key in env.cr.fetchall():
            if KEY_CRYPT_CONTEXT.verify(token, stored_key):
                return user_id
    # Enterprise or base_rest_api addon
    if "api.key" in env:
        rec = env["api.key"].search([("key", "=", token)], limit=1)
        if rec:
            return rec.user_id.id
    return False


def _auth_required():
    header = request.httprequest.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise Unauthorized("Missing Bearer token")
    token = header.split(" ", 1)[1]
    user_id = _get_api_key(request.env, token)
    if not user_id:
        raise Unauthorized("Invalid API token")
    return request.env(user=user_id)


def _paginate(records, limit, offset):
    total = len(records)
    limit = int(limit) if limit else total
    offset = int(offset) if offset else 0
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "records": records[offset: offset + limit],
    }


def _bad(msg):
    raise BadRequest(msg)


# --------------------------------------------------------------
# helpers to accept both JSON-RPC and plain JSON bodies
# --------------------------------------------------------------


def _payload_http():
    """Parse JSON payload for HTTP routes."""
    try:
        data = request.httprequest.get_data(as_text=True)
        if not data:
            return {}
        return json.loads(data)
    except (json.JSONDecodeError, ValueError) as e:
        raise BadRequest(f"Invalid JSON: {str(e)}")


def _payload(in_payload):
    """Return the request body as dict for JSON routes.
    Be forgiving: accept JSON-RPC, dict, or a raw string (even if multiple JSON
    objects were concatenated, we try to parse the last one).
    """
    if in_payload:
        return in_payload

    # Try to get JSON data from request
    try:
        if hasattr(request, 'jsonrequest') and request.jsonrequest:
            body = request.jsonrequest
        else:
            body = request.get_json() if hasattr(request, 'get_json') else None
    except Exception as e:
        logging.getLogger(__name__).error(f"Error parsing JSON: {e}")
        body = None

    if isinstance(body, dict):
        # Handle JSON-RPC format
        if body.get("jsonrpc") and "params" in body:
            return body.get("params", {})
        # Handle plain JSON
        return body

    # Accept raw string bodies and attempt recovery if multiple JSON objs came in
    if isinstance(body, str):
        s = body.strip()
        try:
            return json.loads(s)
        except Exception:
            last_open = s.rfind('{')
            last_close = s.rfind('}')
            if last_open != -1 and last_close != -1 and last_close > last_open:
                candidate = s[last_open:last_close + 1]
                try:
                    return json.loads(candidate)
                except Exception:
                    return {}
            return {}

    return {}


class CustomAPI(http.Controller):
    # Leads ------------------------------------------------------------------
    @http.route(f"{API_PREFIX}/leads", methods=["POST"], type="json", auth="none", csrf=False)
    def create_lead(self, **payload):
        payload = _payload(payload)
        env = _auth_required()

        # Helper to get value with fallback
        def _get(key, default=None):
            return payload.get(key, default)

        # Helper to extract numeric value from string
        def _float(val):
            try:
                return float(val) if val else 0.0
            except (ValueError, TypeError):
                return 0.0

        def _int(val):
            try:
                if isinstance(val, str):
                    # Extract digits from strings like "3 years"
                    digits = "".join(ch for ch in val if ch.isdigit())
                    return int(digits) if digits else 0
                return int(val) if val else 0
            except (ValueError, TypeError):
                return 0

        # Helper to filter out None and empty values
        def _clean_vals(vals_dict):
            """Remove None and empty string values from dict, but keep False for Many2one fields"""
            cleaned = {}
            for k, v in vals_dict.items():
                # Keep False values (valid for Many2one fields)
                if v is False:
                    cleaned[k] = v
                # Skip None and empty strings
                elif v is not None and v != "":
                    cleaned[k] = v
            return cleaned

        # Normalize customer_type
        ctype_raw = (_get("customer_type") or "").lower().strip()
        ctype_map = {
            "consumer": "individual",
            "corporate": "company",
            "cooperate": "company",  # common typo
            "individual": "individual",
            "company": "company",
        }
        ctype = ctype_map.get(ctype_raw)

        # Collect document URLs into arrays from flat payload
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

        # Collect all document URLs from flat payload keys
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

        if not ctype:
            vals.pop("customer_type", None)

        # Handle loan_type_id (required for showing in Loan Leads menu)
        if _get("loan_type_id") is not None:
            try:
                vals["loan_type_id"] = int(_get("loan_type_id"))
            except Exception:
                _bad("Invalid loan_type_id")

        # Support resolving loan_type from XMLID
        if _get("loan_type_xmlid") and not vals.get("loan_type_id"):
            try:
                vals["loan_type_id"] = env.ref(_get("loan_type_xmlid")).id
            except Exception:
                _bad("Invalid loan_type_xmlid")

        # Corporate vs Individual mapping
        if ctype == "company":
            # Corporate fields from flat payload
            comp_name = _get("company_name") or _get("reference") or _get("purpose") or "Company"
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
                # Director fields from flat payload
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
            # Individual/Consumer fields from flat payload
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
                # Next of Kin from flat payload
                "nok_name": _get("next_of_kin_name"),
                "nok_phone": _get("next_of_kin_phone"),
                "nok_address": _get("next_of_kin_address"),
                "nok_relationship": _get("next_of_kin_relationship"),
                "nok_occupation": _get("next_of_kin_occupation"),
                "nok_email": _get("next_of_kin_email"),
                # Employment from flat payload
                "company_name": _get("employment_company_name"),
                "company_email": _get("employment_company_email"),
                "company_address": _get("employment_company_address"),
                "salary": _float(_get("employment_salary")),
                "service_length": _int(_get("employment_length_of_service")),
                "designation": _get("employment_designation"),
            }
            vals.update(_clean_vals(indiv_vals))

        # Always ensure lead has a name
        vals["name"] = vals.get("name") or _get("reference") or "Lead"

        # Guarantor fields (common to both) from flat payload
        guar_vals = {
            "guarantor_title": _get("guarantor_title"),
            "guarantor_name": _get("guarantor_name"),
            "guarantor_phone": _get("guarantor_phone"),
            "guarantor_email": _get("guarantor_email"),
            "guarantor_relationship": _get("guarantor_relationship"),
        }
        vals.update(_clean_vals(guar_vals))

        # Clean all vals before creating (remove None and empty strings)
        vals = _clean_vals(vals)

        # Create partner first if we have enough info, then set partner_id during lead creation
        partner_id = False
        if ctype == "company":
            partner_name = _get("company_name") or _get("reference") or "Company"
            # Try to find existing partner
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
            # Individual - try to find by email or phone
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

        # Set partner_id in vals if we have one
        if partner_id:
            vals["partner_id"] = partner_id

        # Create lead
        lead = env["crm.lead"].sudo().create(vals)

        # Ensure partner is linked (in case creation didn't set it)
        if not lead.partner_id and partner_id:
            lead.sudo().write({"partner_id": partner_id})

        return {
            "id": lead.id,
            "partner_id": lead.partner_id.id if lead.partner_id else partner_id,
            "customer_type": lead.customer_type,
        }

    @http.route(f"{API_PREFIX}/leads", methods=["GET"], type="json", auth="none", csrf=False)
    def list_leads(self, **params):
        env = _auth_required()
        domain = [("type", "=", "lead")]
        if params.get("user_id"):
            domain.append(("user_id", "=", int(params["user_id"])))
        leads = env["crm.lead"].sudo().search(domain)
        return _paginate(leads.read(["id", "name", "email_from", "phone", "active"]), params.get("limit"),
                         params.get("offset"))

    @http.route(f"{API_PREFIX}/opportunities", methods=["GET"], type="json", auth="none", csrf=False)
    def list_opps(self, **params):
        env = _auth_required()
        domain = [("type", "=", "opportunity")]
        if params.get("user_id"):
            domain.append(("user_id", "=", int(params["user_id"])))
        opps = env["crm.lead"].sudo().search(domain)
        return _paginate(opps.read(["id", "name", "stage_id", "expected_revenue"]), params.get("limit"),
                         params.get("offset"))

    # Quotes ----------------------------------------------------------------
    

    

    

    # (all other endpoints removed)