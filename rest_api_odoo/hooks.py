# -*- coding: utf-8 -*-

def pre_init_hook(cr):
    """
    Pre-init hook to clean up the wallet_currency column in res_partner.
    Since we are changing it from Char to Many2one (Integer), existing 'NGN' strings
    will cause the upgrade to fail. This clears the column so Odoo can change the type safely.
    """
    # Check if the column exists first
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'res_partner' AND column_name = 'wallet_currency'
    """)
    if cr.fetchone():
        cr.execute("UPDATE res_partner SET wallet_currency = NULL")
