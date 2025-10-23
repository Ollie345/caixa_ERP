# Custom REST API Documentation

## Configuration

**Base URL:**
```
http://5.189.145.29:8069/custom/api/v1
```

**Headers (all requests):**
```
'Authorization': 'Bearer fb3e312fdd4c946f3ca2f969efbefabe584b8559'
'Content-Type': 'application/json'
```

## Authentication

The API uses Bearer token authentication. You'll need to obtain an API key from your Odoo instance administrator. The token should be included in the Authorization header for all requests.

## 1.0 Leads

### 1.1 Create Lead
**Type:** POST  
**Endpoint:** `http://5.189.145.29:8069/custom/api/v1/leads`

**Body:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "name": "Acme Corp",
    "email": "jane@acme.com",
    "phone": "+2348012345678",
    "user_id": 2
  }
}
```

**Response (201 Created):**
```json
{
    "jsonrpc": "2.0",
    "id": null,
    "result": {
        "id": 1,
        "name": "Acme Corp",
        "email": "jane@acme.com",
        "phone": "+2348012345678",
        "user_id": 2,
        "create_date": "2025-08-25T08:30:08.518501",
        "active": true
    }
}
```

### 1.2 Update Lead
**Type:** PUT  
**Endpoint:** `http://5.189.145.29:8069/custom/api/v1/leads/{lead_id}`

**Body:**
```json
{
    "name": "Acme Corp",
    "email_from": "jane@acme.com",
    "phone": "+2348087654321",
    "description": "Additional notes about the lead"
}
```

**Response (200 OK):** Updated lead object

### 1.3 Get Lead
**Type:** GET  
**Endpoint:** `http://5.189.145.29:8069/custom/api/v1/leads/{lead_id}`

**Response (200 OK):** Lead object

### 1.4 List & Filter Leads
**Type:** GET  
**Endpoint:** `http://5.189.145.29:8069/custom/api/v1/leads?limit=100&offset=20&user_id=2`

**Response (200 OK):**
```json
{
    "jsonrpc": "2.0",
    "id": null,
    "result": {
        "total": 1,
        "limit": 1,
        "offset": 0,
        "records": [
            {
                "id": 1,
                "name": "Acme Corp",
                "email_from": "jane@acme.com",
                "phone": "+2348012345678",
                "active": true
            }
        ]
    }
}
```

## 2.0 Opportunities

### 2.1 Create Opportunity
**Type:** POST  
**Endpoint:** `http://5.189.145.29:8069/custom/api/v1/opportunities`

**Body:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "name": "New Deal Opportunity",
        "expected_revenue": 50000.00,
        "partner_id": 3,
        "probability": 75,
        "user_id": 2
    }
}
```

**Response (201 Created):**
```json
{
    "jsonrpc": "2.0",
    "id": null,
    "result": {
        "id": 3,
        "name": "New Deal Opportunity",
        "expected_revenue": 50000.0,
        "probability": 75.0,
        "user_id": 2,
        "create_date": "2025-08-25T08:58:06.581484",
        "stage_id": 1
    }
}
```

### 2.2 Update Opportunity
**Type:** PUT  
**Endpoint:** `http://5.189.145.29:8069/custom/api/v1/opportunities/{opportunity_id}`

**Body:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "name": "New Opportunity Name",
        "expected_revenue": 75000.00,
        "probability": 90,
        "description": "Updated opportunity details"
    }
}
```

**Response (200 OK):** Updated opportunity object

### 2.3 Get Opportunity
**Type:** GET  
**Endpoint:** `http://5.189.145.29:8069/custom/api/v1/opportunities/{opportunity_id}`

**Response (200 OK):** Opportunity object

### 2.4 Move Pipeline Stage
**Type:** PATCH  
**Endpoint:** `http://5.189.145.29:8069/custom/api/v1/opportunities/{opportunity_id}/stage`

**Body:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "stage_id": 3
    }
}
```

**Response (200 OK):** Opportunity with updated stage_id

### 2.5 List & Filter Opportunities
**Type:** GET  
**Endpoint:** `http://5.189.145.29:8069/custom/api/v1/opportunities?limit=50&offset=20&user_id=2`

**Response (200 OK):**
```json
{
    "jsonrpc": "2.0",
    "id": null,
    "result": {
        "total": 2,
        "limit": 2,
        "offset": 0,
        "records": [
            {
                "id": 3,
                "name": "New Deal Opportunity",
                "stage_id": [
                    1,
                    "New"
                ],
                "expected_revenue": 50000.0
            },
            {
                "id": 2,
                "name": "New Opportunity Name",
                "stage_id": [
                    3,
                    "Proposition"
                ],
                "expected_revenue": 75000.0
            }
        ]
    }
}
```

## 3.0 Sales Quotes

### 3.1 Create Quote
**Type:** POST  
**Endpoint:** `http://5.189.145.29:8069/custom/api/v1/quotes`

**Body:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "partner_id": 3,
        "validity_date": "2025-12-31",
        "order_line": [
            {
                "product_id": 2,
                "product_uom_qty": 3,
                "name": ""
            }
        ]
    }
}
```

**Response (201 Created):**
```json
{
    "jsonrpc": "2.0",
    "id": null,
    "result": {
        "id": 3,
        "name": "S00006",
        "partner_name": "Administrator",
        "partner_email": "admin@example.com",
        "partner_phone": "",
        "user_id": 2,
        "create_date": "2025-08-25T09:13:42.230399",
        "state": "draft",
        "amount_total": 15000.0
    }
}
```

### 3.2 Get Quote
**Type:** GET  
**Endpoint:** `http://5.189.145.29:8069/custom/api/v1/quotes/1`

**Response (200 OK):** Quote object


### 3.4 List & Filter Quotes
**Type:** GET  
**Endpoint:** `http://5.189.145.29:8069/custom/api/v1/quotes?limit=25&offset=0&state=draft`

**Response (200 OK):**
```json
{
    "jsonrpc": "2.0",
    "id": null,
    "result": {
        "total": 3,
        "limit": 3,
        "offset": 0,
        "records": [
            {
                "id": 3,
                "name": "S00006",
                "state": "draft",
                "validity_date": "2025-12-31"
            },
            {
                "id": 2,
                "name": "S00005",
                "state": "draft",
                "validity_date": "2025-12-31"
            },
            {
                "id": 1,
                "name": "S00003",
                "state": "draft",
                "validity_date": "2025-12-31"
            }
        ]
    }
}
```

## 4.0 Activities

### 4.1 List Activity Logs
**Type:** GET  
**Endpoint:** `http://5.189.145.29:8069/custom/api/v1/activities`

**Response (200 OK):**
```json
{
  "total": 25,
  "limit": 50,
  "offset": 0,
  "records": [
    {
      "id": 1001,
      "author_id": 5,
      "date": "2025-07-29T14:30:00Z",
      "message": "Lead created from website form"
    }
  ]
}
```

## Error Handling

The API returns standard HTTP status codes:

- **200 OK:** Successful operation
- **201 Created:** Resource created successfully
- **400 Bad Request:** Invalid request data
- **401 Unauthorized:** Invalid or missing API token
- **404 Not Found:** Resource not found

## Pagination

List endpoints support pagination with `limit` and `offset` query parameters:

- `limit`: Maximum number of records to return (default: all records)
- `offset`: Number of records to skip (default: 0)

## Notes

- All dates are returned in ISO 8601 format
- The API automatically assigns ERP IDs to leads and opportunities
- User IDs must be valid Odoo user IDs
- Partner IDs must be valid customer/partner records
- Product IDs must be valid product records
- All monetary values are in the company's default currency

## Example Usage

### Python Example
```python
import requests

base_url = "http://5.189.145.29:8069/custom/api/v1"
headers = {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
}

# Create a lead
lead_data = {
    "name": "New Company",
    "email": "contact@newcompany.com",
    "phone": "+1234567890"
}

response = requests.post(f"{base_url}/leads", json=lead_data, headers=headers)
if response.status_code == 201:
    lead = response.json()
    print(f"Lead created with ID: {lead['id']}")
```

### JavaScript Example
```javascript
const baseUrl = 'http://5.189.145.29:8069/custom/api/v1';
const headers = {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
};

// Create an opportunity
const opportunityData = {
    name: "Big Deal",
    expected_revenue: 100000,
    probability: 75,
    user_id: 5
};

fetch(`${baseUrl}/opportunities`, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(opportunityData)
})
.then(response => response.json())
.then(data => console.log('Opportunity created:', data));
```
