from odoo import models, fields, api, _
from odoo.exceptions import UserError

class DevLoanClosureWizard(models.TransientModel):
    _name = 'dev.loan.closure.wizard'
    _description = 'Wizard for Early Loan Closure'

    loan_id = fields.Many2one(
        'dev.loan.loan',
        string='Loan',
        required=True,
        readonly=True,
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='loan_id.currency_id',
        readonly=True,
    )

    closure_date = fields.Date(
        string="Closure Date",
        tracking=True
    )

    closure_amount = fields.Monetary(
        string="Closure Amount",
        compute="_compute_closure_amount",
        store=True,
        tracking=True
    )

    is_early_closure = fields.Boolean(
        string="Early Closure",
        default=True  # Set to True since this wizard is specifically for early closure
    )

    # Outstanding principal used for early closure computation
    balance_amount = fields.Monetary(
        string='Outstanding Principal',
        related='loan_id.balance_amount',  # Changed from compute to related
        readonly=True,
    )

    #compute closure amount
    @api.depends('closure_date', 'loan_id', 'loan_id.balance_amount', 'loan_id.installment_ids', 'loan_id.installment_ids.state', 'loan_id.interest_rate')
    def _compute_closure_amount(self):
        """Compute the closure amount for early closure.

        Uses outstanding principal (balance_amount) plus pro‑rated interest
        from the last PAID installment date up to the selected closure_date.
        """
        for wizard in self:  # Changed variable name from 'loan' to 'wizard' for clarity
            wizard.closure_amount = 0.0

            if not wizard.is_early_closure or not wizard.closure_date or not wizard.loan_id:
                continue

            loan = wizard.loan_id  # Get the actual loan record

            if loan.balance_amount <= 0:
                continue

            # Get last PAID installment
            paid_installments = loan.installment_ids.filtered(
                lambda ins: ins.state == 'paid'
            )

            if not paid_installments:
                raise UserError(_("No paid installment found."))

            # Use the installment's 'date' field
            last_installment = max(
                paid_installments,
                key=lambda ins: ins.date
            )

            # Days elapsed from last installment date to closure date
            days_elapsed = (wizard.closure_date - last_installment.date).days
            days_elapsed = min(max(days_elapsed, 0), 30)

            # Interest calculation
            monthly_rate = loan.interest_rate / 100
            daily_rate = monthly_rate / 30

            interest = loan.balance_amount * daily_rate * days_elapsed

            wizard.closure_amount = loan.balance_amount + interest

    # button action to confirm early closure
    def action_confirm_early_closure(self):
        """Post journal entry and close loan for early closure."""
        self.ensure_one()  # Wizards typically work with single records
        
        wizard = self
        loan = wizard.loan_id  # Get the actual loan record

        if not wizard.is_early_closure:
            raise UserError(_("This is not an early closure."))

        if wizard.closure_amount <= 0:
            raise UserError(_("Closure amount not computed."))

        # Use an existing journal from the loan or its type instead of a non-existent company field
        journal = loan.disburse_journal_id or (loan.loan_type_id and loan.loan_type_id.loan_payment_journal_id)
        if not journal:
            raise UserError(
                _("Loan journal not configured. Please set a disburse journal or payment journal on the loan type."))

        move = self.env['account.move'].create({
            'journal_id': journal.id,
            'date': wizard.closure_date,
            'ref': f"Early Closure - {loan.name}",
            'line_ids': [
                (0, 0, {
                    # Use borrower (client_id) receivable account
                    'account_id': loan.client_id.property_account_receivable_id.id,
                    'debit': wizard.closure_amount,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'account_id': loan.loan_account_id.id,
                    'credit': wizard.closure_amount,
                    'debit': 0.0,
                }),
            ]
        })

        move.action_post()

        # Update loan record with closure information
        loan.write({
            'state': 'close',
            'closure_date': wizard.closure_date,
            'closure_amount': wizard.closure_amount,
            'is_early_closure': True,
        })
        loan._send_closure_email()