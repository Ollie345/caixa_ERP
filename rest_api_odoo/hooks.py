# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)

def pre_init_hook(cr):
    """
    Pre-init hook to drop the wallet_currency column in res_partner.
    Since we are changing it from Char to Many2one (Integer), existing 'NGN' strings
    cause the upgrade to fail. Dropping the column allows Odoo to recreate it correctly.
    """
    _logger.info("BaaS Migration: Starting pre_init_hook to handle wallet_currency type change.")
    
    # Check if the column exists
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'res_partner' AND column_name = 'wallet_currency'
    """)
    if cr.fetchone():
        _logger.info("BaaS Migration: Dropping legacy Char column 'wallet_currency' from 'res_partner' table.")
        # Drop the column. Odoo will recreate it as integer during model initialization.
        cr.execute("ALTER TABLE res_partner DROP COLUMN wallet_currency")
        _logger.info("BaaS Migration: Column dropped successfully.")
    else:
        _logger.info("BaaS Migration: Column 'wallet_currency' not found, nothing to drop.")
