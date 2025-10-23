# -*- coding: utf-8 -*-
import json
import logging
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized
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
    """Return the request body as dict for JSON routes."""
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
        return {}

    if isinstance(body, dict):
        # Handle JSON-RPC format
        if body.get("jsonrpc") and "params" in body:
            return body.get("params", {})
        # Handle plain JSON
        return body

    return {}


class CustomAPI(http.Controller):
    # Leads ------------------------------------------------------------------
    @http.route(f"{API_PREFIX}/leads", methods=["POST"], type="json", auth="none", csrf=False)
    def create_lead(self, **payload):
        payload = _payload(payload)
        env = _auth_required()
        if "name" not in payload:
            _bad("name is required")
        vals = {
            "name": payload.get("name"),
            "email_from": payload.get("email"),
            "phone": payload.get("phone"),
            "user_id": payload.get("user_id"),
            "partner_id": payload.get("partner_id"),
            "type": "lead",
        }

        for k in LOAN_LEAD_FIELDS:
            if k in payload and payload[k] is not None:
                vals[k] = payload[k]

        if payload.get("loan_type_xmlid") and not vals.get("loan_type_id"):
            try:
                vals["loan_type_id"] = env.ref(payload["loan_type_xmlid"]).id
            except Exception:
                _bad("Invalid loan_type_xmlid")

        def _to_int(value):
            if isinstance(value, str) and value.isdigit():
                return int(value)
            return value

        if "partner_id" in vals:
            vals["partner_id"] = _to_int(vals["partner_id"])
        if "loan_type_id" in vals:
            vals["loan_type_id"] = _to_int(vals["loan_type_id"])

        # partner_tin is now Char; no coercion needed

        lead = env["crm.lead"].sudo().create(vals)

        # Return data directly, not wrapped in make_json_response
        return {
            "id": lead.id,
            "name": lead.name,
            "email": lead.email_from or "",
            "phone": lead.phone or "",
            "user_id": lead.user_id.id if lead.user_id else None,
            "create_date": lead.create_date.isoformat() if lead.create_date else None,
            "active": lead.active,
        }

    @http.route(f"{API_PREFIX}/leads/<int:lead_id>", methods=["PUT"], type="json", auth="none", csrf=False)
    def update_lead(self, lead_id, **payload):
        payload = _payload(payload)
        env = _auth_required()
        lead = env["crm.lead"].sudo().browse(lead_id)
        if not lead.exists():
            raise NotFound("Lead not found")
        lead.write(payload)
        return lead.read()[0]

    @http.route(f"{API_PREFIX}/leads/<int:lead_id>", methods=["GET"], type="json", auth="none", csrf=False)
    def get_lead(self, lead_id):
        """Retrieve a single lead."""
        env = _auth_required()
        lead = env["crm.lead"].sudo().browse(lead_id)
        if not lead.exists():
            raise NotFound("Lead not found")
        return lead.read()[0]

    @http.route(f"{API_PREFIX}/leads", methods=["GET"], type="json", auth="none", csrf=False)
    def list_leads(self, **params):
        env = _auth_required()
        domain = [("type", "=", "lead")]
        if params.get("user_id"):
            domain.append(("user_id", "=", int(params["user_id"])))
        leads = env["crm.lead"].sudo().search(domain)
        return _paginate(leads.read(["id", "name", "email_from", "phone", "active"]), params.get("limit"),
                         params.get("offset"))

    # Opportunities ---------------------------------------------------------
    @http.route(f"{API_PREFIX}/opportunities", methods=["POST"], type="json", auth="none", csrf=False)
    def create_opp(self, **payload):
        payload = _payload(payload)
        env = _auth_required()
        if "name" not in payload:
            _bad("name required")
        vals = {
            "name": payload["name"],
            "expected_revenue": payload.get("expected_revenue", 0.0),
            "probability": payload.get("probability", 0),
            "user_id": payload.get("user_id"),
            "type": "opportunity",
        }
        opp = env["crm.lead"].sudo().create(vals)

        # Return formatted response
        return {
            "id": opp.id,
            "name": opp.name,
            "expected_revenue": opp.expected_revenue,
            "probability": opp.probability,
            "user_id": opp.user_id.id if opp.user_id else None,
            "create_date": opp.create_date.isoformat() if opp.create_date else None,
            "stage_id": opp.stage_id.id if opp.stage_id else None,
        }

    @http.route(f"{API_PREFIX}/opportunities/<int:opp_id>", methods=["PUT"], type="json", auth="none", csrf=False)
    def update_opp(self, opp_id, **payload):
        payload = _payload(payload)
        env = _auth_required()
        opp = env["crm.lead"].sudo().browse(opp_id)
        if not opp.exists():
            raise NotFound("Opportunity not found")
        opp.write(payload)
        return opp.read()[0]

    @http.route(f"{API_PREFIX}/opportunities/<int:opp_id>", methods=["GET"], type="json", auth="none", csrf=False)
    def get_opp(self, opp_id):
        """Retrieve a single opportunity."""
        env = _auth_required()
        opp = env["crm.lead"].sudo().browse(opp_id)
        if not opp.exists():
            raise NotFound("Opportunity not found")
        return opp.read()[0]

    @http.route(f"{API_PREFIX}/opportunities/<int:opp_id>/stage", methods=["PATCH"], type="json", auth="none",
                csrf=False)
    def move_stage(self, opp_id, stage_id=None, **kwargs):
        """Move an opportunity to a new stage."""
        env = _auth_required()

        # Retrieve stage_id from query or body
        if stage_id is None:
            stage_id = kwargs.get("stage_id")

        if not stage_id:
            raise BadRequest("stage_id required")

        opp = env["crm.lead"].sudo().browse(opp_id)
        if not opp.exists():
            raise NotFound("Opportunity not found")

        opp.write({"stage_id": int(stage_id)})
        return opp.read()[0]

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
    @http.route(f"{API_PREFIX}/quotes", methods=["POST"], type="json", auth="none", csrf=False)
    def create_quote(self, **payload):
        payload = _payload(payload)
        env = _auth_required()

        # Debug: Log what we received
        _logger = logging.getLogger(__name__)
        _logger.info(f"Received payload: {payload}")
        _logger.info(f"Payload keys: {list(payload.keys()) if payload else 'None'}")

        if not payload:
            _bad("No data received")
        if "order_line" not in payload:
            _bad(f"order_line required. Received keys: {list(payload.keys())}")
        vals = {
            "partner_id": payload.get("partner_id") or env.user.partner_id.id,
            "validity_date": payload.get("validity_date"),
            "order_line": [(0, 0, line) for line in payload["order_line"]],
        }

        so = env["sale.order"].sudo().create(vals)

        # Return data directly - this is the key fix!
        return {
            "id": so.id,
            "name": so.name,
            "partner_name": so.partner_id.name,
            "partner_email": so.partner_id.email or "",
            "partner_phone": so.partner_id.phone or "",
            "user_id": so.user_id.id if so.user_id else None,
            "create_date": so.create_date.isoformat() if so.create_date else None,
            "state": so.state,
            "amount_total": so.amount_total,
        }

    @http.route(f"{API_PREFIX}/quotes/<int:quote_id>", methods=["GET"], type="json", auth="none", csrf=False)
    def get_quote(self, quote_id):
        env = _auth_required()
        so = env["sale.order"].sudo().browse(quote_id)
        if not so.exists():
            raise NotFound("Quote not found")
        return so.read()[0]

    @http.route(f"{API_PREFIX}/quotes", methods=["GET"], type="json", auth="none", csrf=False)
    def list_quotes(self, **params):
        env = _auth_required()
        domain = []
        if params.get("state"):
            domain.append(("state", "=", params["state"]))
        quotes = env["sale.order"].sudo().search(domain)
        return _paginate(quotes.read(["id", "name", "state", "validity_date"]), params.get("limit"),
                         params.get("offset"))

    # Test endpoint to debug payload issues
    @http.route(f"{API_PREFIX}/test", methods=["POST"], type="json", auth="none", csrf=False)
    def test_payload(self, **payload):
        try:
            payload = _payload(payload)
            return {
                "received_payload": payload,
                "payload_type": type(payload).__name__,
                "keys": list(payload.keys()) if isinstance(payload, dict) else [],
                "has_order_line": "order_line" in payload if isinstance(payload, dict) else False,
                "raw_payload": str(payload)
            }
        except Exception as e:
            return {"error": str(e), "type": type(e).__name__}

    # Activities ------------------------------------------------------------
    @http.route(f"{API_PREFIX}/activities", methods=["GET"], type="json", auth="none", csrf=False)
    def list_activities(self, model, res_id, **params):
        env = _auth_required()
        msgs = env["mail.message"].sudo().search([("model", "=", model), ("res_id", "=", int(res_id))],
                                                 order="date desc")
        result = [
            {"id": m.id, "author_id": m.author_id.id if m.author_id else False, "date": m.date.isoformat(),
             "message": m.body or ""}
            for m in msgs
        ]
        return _paginate(result, params.get("limit"), params.get("offset"))