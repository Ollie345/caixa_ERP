# REST API Odoo - Setup & Testing Guide

## 📋 Table of Contents
1. [Odoo Setup](#odoo-setup)
2. [Generate API Key](#generate-api-key)
3. [Configure Models](#configure-models)
4. [Postman Testing](#postman-testing)
5. [Testing Loan Leads Endpoint](#testing-loan-leads-endpoint)

---

## 🚀 Odoo Setup

### Step 1: Install/Upgrade Module

1. **Open Odoo Apps Menu**
   - Go to: `Apps` → Search for `rest_api_odoo` or `Odoo rest API`
   - Click `Install` (or `Upgrade` if already installed)

2. **Alternative: Command Line**
   ```bash
   ./odoo-bin -u rest_api_odoo -d your_database_name
   ```

3. **Restart Odoo** (if needed)
   ```bash
   # Stop Odoo, then restart
   ./odoo-bin -c odoo.conf
   ```

---

## 🔑 Generate API Key

### Step 1: Get API Key via Endpoint

**Method 1: Using Postman (Recommended)**

1. **Create New Request**
   - Method: `GET`
   - URL: `http://localhost:8069/odoo_connect`
   - (Replace `localhost:8069` with your Odoo URL)

2. **Add Headers:**
   ```
   db: your_database_name
   login: your_username
   password: your_password
   ```

3. **Send Request**
   - You'll receive a response like:
   ```json
   {
     "Status": "auth successful",
     "User": "Administrator",
     "api-key": "4314c30b-994e-435d-a493-50cb0d33e99d"
   }
   ```

4. **Save the API Key** - You'll need it for all subsequent requests!

**Method 2: Check User Settings**

- Go to: `Settings` → `Users & Companies` → `Users`
- Open your user
- Check the `API Key` field (it's generated automatically after first `/odoo_connect` call)

---

## ⚙️ Configure Models

### Step 1: Access REST API Configuration

1. **Go to REST API Menu**
   - Navigate to: `Rest API` → `Rest API` (in main menu)
   - Or search for "Rest API Records" in Apps

2. **Create New Configuration**
   - Click `Create` button
   - Select a `Model` (e.g., `crm.lead`, `res.partner`, etc.)
   - Enable the methods you want:
     - ✅ `GET` - Read records
     - ✅ `POST` - Create records
     - ✅ `PUT` - Update records
     - ✅ `DELETE` - Delete records

3. **Example Configurations:**

   **For CRM Leads:**
   - Model: `crm.lead`
   - Enable: GET, POST, PUT, DELETE

   **For Partners:**
   - Model: `res.partner`
   - Enable: GET, POST, PUT, DELETE

4. **Save** the configuration

---

## 📮 Postman Testing

### Setup Postman Environment (Optional but Recommended)

1. **Create Environment**
   - Click `Environments` → `+` → Name it "Odoo REST API"

2. **Add Variables:**
   ```
   base_url: http://localhost:8069
   db: your_database_name
   login: your_username
   password: your_password
   api_key: <paste_your_api_key_here>
   ```

3. **Use Variables in Requests:**
   - URL: `{{base_url}}/send_request`
   - Headers: `{{api_key}}`, `{{login}}`, `{{password}}`

---

### Test 1: GET Records

**Request:**
```
Method: GET
URL: http://localhost:8069/send_request?model=crm.lead&Id=1
```

**Headers:**
```
login: your_username
password: your_password
api-key: your_api_key
```

**Body (raw JSON):**
```json
{
    "fields": ["name", "email_from", "phone", "loan_amount"]
}
```

**Expected Response:**
```json
[
  "{\"records\": [{\"id\": 1, \"name\": \"Lead Name\", \"email_from\": \"test@example.com\", \"phone\": \"1234567890\", \"loan_amount\": 100000.0}]}"
]
```

---

### Test 2: POST (Create) Records

**Request:**
```
Method: POST
URL: http://localhost:8069/send_request?model=crm.lead
```

**Headers:**
```
login: your_username
password: your_password
api-key: your_api_key
```

**Body (raw JSON):**
```json
{
    "fields": ["name", "email_from", "phone"],
    "values": {
        "name": "Test Lead",
        "email_from": "test@example.com",
        "phone": "1234567890",
        "type": "lead"
    }
}
```

**Expected Response:**
```json
[
  "{\"New resource\": [{\"id\": 123, \"name\": \"Test Lead\", \"email_from\": \"test@example.com\", \"phone\": \"1234567890\"}]}"
]
```

---

### Test 3: PUT (Update) Records

**Request:**
```
Method: PUT
URL: http://localhost:8069/send_request?model=crm.lead&Id=123
```

**Headers:**
```
login: your_username
password: your_password
api-key: your_api_key
```

**Body (raw JSON):**
```json
{
    "fields": ["name", "phone"],
    "values": {
        "name": "Updated Lead Name",
        "phone": "9876543210"
    }
}
```

---

### Test 4: DELETE Records

**Request:**
```
Method: DELETE
URL: http://localhost:8069/send_request?model=crm.lead&Id=123
```

**Headers:**
```
login: your_username
password: your_password
api-key: your_api_key
```

**Body:** (Not required for DELETE)

---

## 🎯 Testing Loan Leads Endpoint

### Special Endpoint: `/loan_leads`

This endpoint accepts your **flat payload structure** and handles all field mapping automatically.

### Request Setup

**Method:** `POST`  
**URL:** `http://localhost:8069/loan_leads`

**Headers:**
```
api-key: your_api_key
db: your_database_name
Content-Type: application/json
```

**Body (raw JSON) - Consumer Example:**
```json
{
  "user_id": 2,
  "kyc_id": 12,
  "reference": "LRFC-36434",
  "amount": "100000",
  "tenor": "5",
  "purpose": "Working capital",
  "collateral": "Vehicle",
  "source_of_repayment": "Salary",
  "status": "pending",
  "customer_type": "consumer",
  "loan_type_id": 1,
  "applicant_title": "Mr",
  "applicant_first_name": "John",
  "applicant_middle_name": "Doe",
  "applicant_surname": "Smith",
  "applicant_email": "john@example.com",
  "applicant_phone": "08012345678",
  "applicant_nin": "12345678901",
  "applicant_bvn": "1234567890",
  "applicant_address": "123 Example Street",
  "applicant_marital_status": "single",
  "next_of_kin_name": "Jane Doe",
  "next_of_kin_phone": "08087654321",
  "employment_company_name": "Example Ltd",
  "employment_company_email": "hr@example.com",
  "employment_company_address": "45 Industrial Road",
  "employment_salary": "200000",
  "employment_length_of_service": "3 years",
  "employment_designation": "Accountant",
  "guarantor_title": "Mr",
  "guarantor_name": "Paul",
  "guarantor_phone": "08142555137",
  "guarantor_email": "paul@example.com",
  "guarantor_relationship": "Colleague",
  "kyc_documents_passport": "https://example.com/passport.jpg",
  "kyc_documents_govt_issued_id": "https://example.com/id.jpg",
  "loan_documents_additional_document": "https://example.com/loan_doc.pdf"
}
```

**Body (raw JSON) - Corporate Example:**
```json
{
  "user_id": 5,
  "kyc_id": 13,
  "reference": "LRFC-89082",
  "amount": "100000",
  "tenor": "5",
  "purpose": "Business expansion",
  "collateral": "Property",
  "source_of_repayment": "Revenue",
  "status": "pending",
  "customer_type": "corporate",
  "loan_type_id": 1,
  "company_name": "Example Tech Ltd",
  "company_email": "admin@example.com",
  "company_phone": "08011223344",
  "rc_number": "RC-556677",
  "date_of_incorporation": "2015-03-20",
  "annual_turnover": "50000000",
  "company_address": "10 Adeola Odeku, Lagos",
  "director_title": "Mr",
  "director_first_name": "Michael",
  "director_middle_name": "James",
  "director_surname": "Smith",
  "director_phone": "08033445566",
  "director_email": "michael@example.com",
  "director_nin": "22334455667",
  "director_dob": "1986-05-14",
  "director_bvn": "2244556677",
  "director_address": "24 Lekki Phase 1, Lagos",
  "director_marital_status": "married",
  "director_designation": "Managing Director",
  "guarantor_title": "Mr",
  "guarantor_name": "Paul",
  "guarantor_phone": "08142555137",
  "guarantor_email": "paul@example.com",
  "guarantor_relationship": "Partner",
  "kyc_documents_passport": "https://example.com/passport.jpg",
  "kyc_documents_certificate_of_incorporation": "https://example.com/cert.pdf",
  "loan_documents_contract_award_letter": "https://example.com/contract.pdf"
}
```

**Expected Response:**
```json
{
  "id": 123,
  "partner_id": 456,
  "customer_type": "individual"
}
```

---

## 🔍 Troubleshooting

### Error: "Invalid API Key"
- **Solution:** Regenerate API key using `/odoo_connect` endpoint
- Make sure header name is exactly `api-key` (not `api_key`)

### Error: "No Record Created for the model"
- **Solution:** Go to `Rest API` → `Rest API` menu and create a configuration for that model

### Error: "Method Not Allowed"
- **Solution:** Enable the method (GET/POST/PUT/DELETE) in the model configuration

### Error: "Invalid JSON Data"
- **Solution:** Check your JSON syntax. Use a JSON validator if needed.

### Error: "Invalid model"
- **Solution:** Make sure the model name is correct (e.g., `crm.lead`, not `crm_lead`)

---

## 📝 Quick Reference

### Endpoints:
- **Generate API Key:** `GET /odoo_connect`
- **Generic CRUD:** `GET/POST/PUT/DELETE /send_request?model=<model_name>&Id=<id>`
- **Loan Leads (Custom):** `POST /loan_leads`

### Required Headers:
- `api-key`: Your API key (for all requests except `/odoo_connect`)
- `db`: Database name (required for `/loan_leads` and `/odoo_connect`)
- `login`: Your username (for `/send_request` and `/odoo_connect`)
- `password`: Your password (for `/send_request` and `/odoo_connect`)

### Payload Format:
- **Generic API:** `{"fields": [...], "values": {...}}`
- **Loan Leads API:** Flat structure (all fields at root level)

---

## ✅ Checklist

- [ ] Module installed/upgraded
- [ ] API key generated
- [ ] Model configurations created
- [ ] Postman environment set up
- [ ] Test GET request successful
- [ ] Test POST request successful
- [ ] Test PUT request successful
- [ ] Test DELETE request successful
- [ ] Test `/loan_leads` endpoint successful

---

**Need Help?** Check the module documentation or contact support.

