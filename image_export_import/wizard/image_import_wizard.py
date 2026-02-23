# -*- coding: utf-8 -*-

import base64
import json
import zipfile
from io import BytesIO

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ImageImportWizard(models.TransientModel):
    _name = 'image.import.wizard'
    _description = 'Import Images Wizard'

    import_file = fields.Binary(
        'Import File (ZIP)',
        required=True,
        help='Upload the ZIP file exported from another Odoo database'
    )
    filename = fields.Char('Filename')
    preview_data = fields.Text('Preview Data', readonly=True)
    export_info = fields.Text('Export Information', readonly=True)
    state = fields.Selection([
        ('upload', 'Upload'),
        ('preview', 'Preview'),
        ('done', 'Done')
    ], default='upload', string='State')
    
    match_by = fields.Selection([
        ('id', 'By ID (same database)'),
        ('external_id', 'By External ID'),
        ('name', 'By Name/Display Name')
    ], default='external_id', string='Match Records By', required=True,
       help='How to match exported records with records in this database')

    @api.onchange('import_file')
    def _onchange_import_file(self):
        """Preview the import file when uploaded"""
        if not self.import_file:
            return
        
        try:
            # Decode the file
            zip_data = base64.b64decode(self.import_file)
            zip_buffer = BytesIO(zip_data)
            
            with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
                # Read export info
                if 'export_info.json' in zip_file.namelist():
                    info_data = zip_file.read('export_info.json')
                    export_info = json.loads(info_data.decode('utf-8'))
                    self.export_info = json.dumps(export_info, indent=2)
                else:
                    self.export_info = 'No export information found.'
                
                # Read mapping
                if 'mapping.json' in zip_file.namelist():
                    mapping_data = zip_file.read('mapping.json')
                    mapping = json.loads(mapping_data.decode('utf-8'))
                    
                    # Create preview
                    preview_lines = [
                        f"Model: {export_info.get('model', 'Unknown')}",
                        f"Records: {export_info.get('record_count', 0)}",
                        f"Image Fields: {', '.join(export_info.get('image_fields', []))}",
                        f"Images to Import: {len(mapping)}",
                        "",
                        "Sample records:"
                    ]
                    
                    # Show first 10 records
                    seen_records = set()
                    for item in mapping[:20]:
                        record_key = f"{item.get('model')}_{item.get('res_id')}"
                        if record_key not in seen_records:
                            preview_lines.append(f"  - {item.get('record_name', 'Unknown')} (ID: {item.get('res_id')})")
                            seen_records.add(record_key)
                    
                    if len(mapping) > 20:
                        preview_lines.append(f"  ... and {len(mapping) - 20} more")
                    
                    self.preview_data = '\n'.join(preview_lines)
                    self.state = 'preview'
                else:
                    raise UserError(_('Invalid export file: mapping.json not found.'))
        
        except zipfile.BadZipFile:
            raise UserError(_('Invalid ZIP file. Please upload a valid export file.'))
        except Exception as e:
            raise UserError(_('Error reading import file: %s') % str(e))

    def action_import(self):
        """Import images from ZIP file"""
        self.ensure_one()
        
        if not self.import_file:
            raise UserError(_('Please upload an import file first.'))
        
        try:
            # Decode the file
            zip_data = base64.b64decode(self.import_file)
            zip_buffer = BytesIO(zip_data)
            
            with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
                # Read mapping
                if 'mapping.json' not in zip_file.namelist():
                    raise UserError(_('Invalid export file: mapping.json not found.'))
                
                mapping_data = zip_file.read('mapping.json')
                mapping = json.loads(mapping_data.decode('utf-8'))
                
                if not mapping:
                    raise UserError(_('No images found in export file.'))
                
                # Group by model
                model_groups = {}
                for item in mapping:
                    model = item.get('model')
                    if model not in model_groups:
                        model_groups[model] = []
                    model_groups[model].append(item)
                
                imported_count = 0
                skipped_count = 0
                error_count = 0
                errors = []
                
                # Process each model
                for model_name, items in model_groups.items():
                    if model_name not in self.env:
                        errors.append(f"Model {model_name} not found in this database")
                        error_count += len(items)
                        continue
                    
                    model = self.env[model_name]
                    
                    # Group by record
                    record_groups = {}
                    for item in items:
                        res_id = item.get('res_id')
                        if res_id not in record_groups:
                            record_groups[res_id] = []
                        record_groups[res_id].append(item)
                    
                    # Find records
                    for res_id, record_items in record_groups.items():
                        record = None
                        
                        # Try to find record based on match_by
                        if self.match_by == 'id':
                            record = model.browse(res_id)
                            if not record.exists():
                                record = None
                        
                        elif self.match_by == 'external_id':
                            external_id = record_items[0].get('external_id')
                            if external_id:
                                try:
                                    record = self.env.ref(external_id, raise_if_not_found=False)
                                except Exception:
                                    pass
                        
                        elif self.match_by == 'name':
                            record_name = record_items[0].get('record_name', '')
                            if record_name:
                                # Try to find by name (this is model-specific)
                                # For products, try by name
                                if model_name == 'product.template':
                                    record = model.search([('name', '=', record_name)], limit=1)
                                elif model_name == 'product.product':
                                    record = model.search([('name', '=', record_name)], limit=1)
                                elif model_name == 'res.partner':
                                    record = model.search([('name', '=', record_name)], limit=1)
                                else:
                                    # Generic search by display_name
                                    record = model.search([('id', '=', res_id)], limit=1)
                        
                        if not record or not record.exists():
                            skipped_count += len(record_items)
                            errors.append(f"Record not found: {record_items[0].get('record_name', 'Unknown')} (ID: {res_id})")
                            continue
                        
                        # Import images for this record
                        for item in record_items:
                            field_name = item.get('field_name')
                            file_path = item.get('file_path')
                            
                            # Skip attachments (they're handled separately)
                            if field_name.startswith('attachment_'):
                                continue
                            
                            if field_name not in model._fields:
                                error_count += 1
                                continue
                            
                            # Read image from ZIP
                            try:
                                image_data = zip_file.read(file_path)
                                image_b64 = base64.b64encode(image_data).decode('utf-8')
                                
                                # Write to record
                                record.write({field_name: image_b64})
                                imported_count += 1
                                
                            except Exception as e:
                                error_count += 1
                                errors.append(f"Error importing {file_path}: {str(e)}")
                
                # Prepare result message
                message_parts = [
                    f"Import completed!",
                    f"Imported: {imported_count} images",
                    f"Skipped: {skipped_count} records",
                    f"Errors: {error_count}",
                ]
                
                if errors and len(errors) <= 10:
                    message_parts.append("\nErrors:")
                    message_parts.extend(errors[:10])
                elif errors:
                    message_parts.append(f"\n{len(errors)} errors occurred (showing first 10)")
                
                self.write({
                    'state': 'done',
                    'preview_data': '\n'.join(message_parts)
                })
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Import Complete'),
                        'message': f'Imported {imported_count} images successfully.',
                        'type': 'success',
                        'sticky': False,
                    }
                }
        
        except zipfile.BadZipFile:
            raise UserError(_('Invalid ZIP file. Please upload a valid export file.'))
        except Exception as e:
            raise UserError(_('Error importing images: %s') % str(e))
