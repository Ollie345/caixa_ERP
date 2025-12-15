# Penalty Testing Guide

This guide walks you through setting up a loan to test the penalty calculation feature.

## Prerequisites

1. Odoo server must be running
2. Module `dev_loan_management_caixa` must be installed
3. You need access to create loans and loan types

## Step-by-Step Setup

### Step 1: Configure Loan Type with Penalty Settings

1. **Navigate to:** Loan Management → Configuration → Loan Type
2. **Create or Edit a Loan Type:**
   - Click "Create" or select an existing loan type
   - Fill in basic information:
     - **Name:** "Test Penalty Loan" (or any name)
     - **Loan Amount Limit:** e.g., ₦100,000
     - **Loan Term By Month:** e.g., 6 months
     - **Interest Rate:** e.g., 12%
     - **Interest Mode:** Flat or Reducing
   - **Go to "Other Details" tab:**
     - **Grace Period (Days):** Set to `3` (default is 3)
     - **Daily Penalty Rate (%):** Set to `5.0` (default is 7.0)
   - **Configure Accounting:** Set required accounts and journals
   - **Save**

**Important:** Note down these values:
- Grace Period: `3 days`
- Penalty Rate: `5.0%`
- Interest Rate: `12%`

### Step 2: Create a Test Borrower (if needed)

1. **Navigate to:** Contacts → Create
2. **Create a partner:**
   - Name: "Test Borrower"
   - Enable "Allow Loan" checkbox
   - Save

### Step 3: Create a Loan Request

1. **Navigate to:** Loan Management → Loan Request → Create
2. **Fill in loan details:**
   - **Borrower:** Select your test borrower
   - **Loan Type:** Select "Test Penalty Loan" (from Step 1)
   - **Loan Amount:** e.g., ₦10,000 (smaller amount for easier testing)
   - **Request Date:** Today's date (or any date)
   - **Loan Purpose:** "Penalty Testing"
   - Fill other required fields
   - **Save**

### Step 4: Submit Loan for Review

1. **Click "Submit for Review"** button
   - Loan state changes to "Review"
   - Installments are calculated (but dates are based on request_date)

### Step 5: Confirm Loan

1. **Click "Confirm Loan"** button
   - Loan state changes to "Confirmed"
   - Installments are recalculated

### Step 6: Approve Loan

1. **Click "Approve Loan"** button
   - Loan state changes to "Approved"
   - Approve Date is set to today
   - **Important:** Now you can see and edit the Disbursement Date field

### Step 7: Set Past Disbursement Date (For Testing)

**This is the key step for testing penalties!**

1. **In the loan form, find "Dates & Status" section**
2. **You should now see "Disbursement Date" field** (editable)
3. **Set Disbursement Date to a past date:**
   - **Example:** If today is December 10, 2025, set it to:
     - **For 10 days overdue:** Set to `November 30, 2025` (40 days ago)
     - **Calculation:** 
       - First installment = Nov 30 + 30 days = Dec 30 (but that's future)
       - Actually: First installment = Disbursement Date + 30 days
       - If disbursement = 40 days ago, first installment = 10 days ago
       - Grace ends = 10 days ago + 3 days = 7 days ago
       - Overdue = 7 days ✓

   **Quick Formula:**
   ```
   Disbursement Date = Today - (30 + Desired Overdue Days + Grace Period)
   
   Example: Want 10 days overdue with 3-day grace:
   Disbursement Date = Today - (30 + 10 + 3) = Today - 43 days
   ```

4. **Save the loan**

### Step 8: Disburse the Loan

1. **Click "Disburse Loan"** button
   - Loan state changes to "Disbursed" then "Open"
   - Installments are recalculated using your past disbursement date
   - First installment date should now be in the past

### Step 9: Verify Installment Dates

1. **Go to "Installments" tab** in the loan form
2. **Check the dates:**
   - First installment date should be: `Disbursement Date + 30 days`
   - If disbursement was 40 days ago, first installment = 10 days ago
   - Subsequent installments are spaced 30 days apart

### Step 10: Calculate Penalties

You have two options:

#### Option A: Manual Calculation (Recommended for Testing)

1. **Open any unpaid installment** from the installments list
2. **Or use Python shell:**
   ```python
   # In Odoo shell
   loan = env['dev.loan.loan'].search([('name', '=', 'LOAN_NAME')], limit=1)
   installments = loan.installment_ids.filtered(lambda i: i.state == 'unpaid')
   installments.compute_penalty()
   ```

#### Option B: Run Cron Job Manually

1. **Navigate to:** Settings → Technical → Automation → Scheduled Actions
2. **Find:** "Compute Loan Penalties"
3. **Click:** "Run Manually"
4. **Check logs** for any errors

### Step 11: Verify Penalty Results

1. **Go back to loan form → Installments tab**
2. **Check the penalty fields:**
   - **Days Overdue:** Should show number of days past grace period
   - **Penalty Amount:** Should show calculated penalty

3. **Manual Verification:**
   ```
   Expected Calculation:
   - Installment Date: 10 days ago
   - Grace Period: 3 days
   - Grace End: 7 days ago
   - Overdue Days: Today - 7 days ago = 7 days
   - Opening Balance: e.g., ₦10,000
   - Interest Rate: 12%
   - Penalty Rate: 5%
   - Daily Rate: (12% + 5%) / 100 = 0.17 = 17%
   - Penalty: ₦10,000 × 0.17 × 7 = ₦11,900
   ```

## Testing Different Scenarios

### Scenario 1: No Penalty (Within Grace Period)

**Setup:**
- Disbursement Date: 2 days ago
- Grace Period: 3 days
- First Installment: 2 days ago + 30 = 28 days in future
- **Result:** No penalty (installment not due yet)

**Better test:**
- Disbursement Date: 32 days ago
- First Installment: 32 days ago + 30 = 2 days ago
- Grace End: 2 days ago + 3 = 1 day ago (yesterday)
- **Result:** Still in grace period, no penalty

### Scenario 2: Small Penalty (Just Overdue)

**Setup:**
- Disbursement Date: 35 days ago
- First Installment: 5 days ago
- Grace End: 2 days ago
- Overdue: 2 days
- **Result:** Small penalty for 2 days

### Scenario 3: Large Penalty (Long Overdue)

**Setup:**
- Disbursement Date: 60 days ago
- First Installment: 30 days ago
- Grace End: 27 days ago
- Overdue: 27 days
- **Result:** Large penalty for 27 days

### Scenario 4: Multiple Overdue Installments

**Setup:**
- Disbursement Date: 70 days ago
- First Installment: 40 days ago (overdue)
- Second Installment: 10 days ago (overdue)
- Third Installment: 20 days in future (not due)
- **Result:** First two installments have penalties

## Quick Test Script

If you prefer to test programmatically, use this script:

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/excitepa/odoo18/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from datetime import date, timedelta

odoo.tools.config.parse_config(['-c', '/home/excitepa/odoo18/odoo/conf/odoo.conf'])
registry = odoo.registry('bpl_test_demo')  # Change to your database

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Find your test loan
    loan = env['dev.loan.loan'].search([('state', '=', 'open')], limit=1)
    
    if not loan:
        print("No open loan found! Please create and disburse a loan first.")
        sys.exit(1)
    
    print(f"Testing penalty for loan: {loan.name}")
    print(f"Grace Period: {loan.grace_period} days")
    print(f"Penalty Rate: {loan.penalty_rate}%")
    print(f"Interest Rate: {loan.interest_rate}%")
    
    # Get unpaid installments
    installments = loan.installment_ids.filtered(lambda i: i.state == 'unpaid')
    
    print(f"\nFound {len(installments)} unpaid installments")
    print("\n=== INSTALLMENT DATES ===")
    for inst in installments[:5]:
        grace_end = inst.date + timedelta(days=loan.grace_period) if inst.date else None
        overdue = (date.today() - grace_end).days if grace_end and date.today() > grace_end else 0
        print(f"  {inst.name}: Date={inst.date}, Grace End={grace_end}, Overdue={overdue} days")
    
    # Calculate penalties
    print("\n=== CALCULATING PENALTIES ===")
    installments.compute_penalty()
    cr.commit()
    
    # Show results
    print("\n=== PENALTY RESULTS ===")
    for inst in installments[:5]:
        print(f"\n{inst.name}:")
        print(f"  Date: {inst.date}")
        print(f"  Opening Balance: {inst.opening_balance}")
        print(f"  Days Overdue: {inst.days_overdue}")
        print(f"  Penalty Amount: {inst.penalty_amount}")
```

## Troubleshooting

### Issue: Penalty Amount is 0

**Possible causes:**
1. Installment is still within grace period
2. Installment date is in the future
3. Grace period is too long
4. Rates are not set correctly

**Solution:** Check:
- Installment date vs today
- Grace period setting
- Loan type penalty rate

### Issue: Penalty Amount seems too high

**Check:** The formula uses `(interest_rate + penalty_rate) / 100` as daily rate.
- This might be intended as annual rate, not daily
- Verify with business requirements

### Issue: Error when calculating penalties

**Check:**
1. All required fields are set (grace_period, penalty_rate, interest_rate)
2. Loan type has penalty settings configured
3. Installments have dates set

## Next Steps

After testing:
1. Verify penalty calculations match your business rules
2. Test cron job runs successfully daily
3. Check penalty amounts in reports
4. Test penalty reset when installments are paid

