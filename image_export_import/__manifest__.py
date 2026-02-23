# -*- coding: utf-8 -*-
{
    'name': 'Image Export/Import',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Export and import images from Odoo records',
    'description': """
Image Export/Import Module
===========================

This module allows you to:
* Export images from selected records (products, partners, etc.)
* Import images back into Odoo records
* Transfer images between Odoo databases

Features:
---------
* Export images via server action from any model with image fields
* Select specific records to export
* Import images from ZIP file with mapping
* Automatic detection of image fields
* Support for all Binary/Image field types
    """,
    'author': 'Olayinka Segun',
    'website': 'https://www.github.com/Olayinka-Segun',
    'depends': ['base', 'web'],
    'external_dependencies': {},
    'data': [
        'security/ir.model.access.csv',
        'data/server_actions.xml',
        'views/menu.xml',
        'wizard/image_export_wizard_views.xml',
        'wizard/image_import_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
