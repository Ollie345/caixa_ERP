# -*- coding: utf-8 -*-

import base64
import json
import zipfile
from io import BytesIO
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ImageExportWizard(models.TransientModel):
    _name = 'image.export.wizard'
    _description = 'Export Images Wizard'

    model_name = fields.Char('Model', readonly=True)
    record_count = fields.Integer('Selected Records', readonly=True)
    image_fields = fields.Many2many(
        'ir.model.fields',
        string='Image Fields',
        domain="[('model_id.model', '=', model_name), ('ttype', 'in', ['binary', 'image'])]",
        help='Select which image fields to export. Leave empty to export all.'
    )
    include_attachments = fields.Boolean(
        'Include Attachments',
        default=False,
        help='Include attachment files linked to selected records'
    )
    export_file = fields.Binary('Export File', readonly=True, attachment=False)
    filename = fields.Char('Filename', readonly=True)
    state = fields.Selection([
        ('config', 'Configuration'),
        ('done', 'Done')
    ], default='config', string='State')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self._context.get('active_model')
        active_ids = self._context.get('active_ids', [])
        
        if not active_model or not active_ids:
            raise UserError(_('Please select records to export images from.'))
        
        res['model_name'] = active_model
        res['record_count'] = len(active_ids)
        
        # Auto-detect image fields
        model = self.env[active_model]
        image_fields = self.env['ir.model.fields'].search([
            ('model_id.model', '=', active_model),
            ('ttype', 'in', ['binary', 'image'])
        ])
        
        if image_fields:
            res['image_fields'] = [(6, 0, image_fields.ids)]
        
        return res

    def action_export(self):
        """Export images from selected records"""
        self.ensure_one()
        
        if not self.model_name or not self._context.get('active_ids'):
            raise UserError(_('No records selected for export.'))
        
        model = self.env[self.model_name]
        record_ids = self._context.get('active_ids', [])
        records = model.browse(record_ids)
        
        # Get image fields to export
        if self.image_fields:
            field_names = self.image_fields.mapped('name')
        else:
            # Export all image fields
            all_image_fields = self.env['ir.model.fields'].search([
                ('model_id.model', '=', self.model_name),
                ('ttype', 'in', ['binary', 'image'])
            ])
            field_names = all_image_fields.mapped('name')
        
        if not field_names:
            raise UserError(_('No image fields found on model %s.') % self.model_name)
        
        # Create ZIP file
        zip_buffer = BytesIO()
        mapping = []
        export_info = {
            'export_date': datetime.now().isoformat(),
            'model': self.model_name,
            'record_count': len(records),
            'image_fields': field_names,
            'include_attachments': self.include_attachments,
        }
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            exported_count = 0
            
            for record in records:
                record_name = record.display_name or f"Record_{record.id}"
                # Sanitize record name for file system
                record_name = "".join(c for c in record_name if c.isalnum() or c in (' ', '-', '_')).strip()
                record_name = record_name.replace(' ', '_')
                
                for field_name in field_names:
                    if field_name not in model._fields:
                        continue
                    
                    field = model._fields[field_name]
                    if field.type not in ('binary', 'image'):
                        continue
                    
                    # Get image data
                    image_data = getattr(record, field_name, False)
                    if not image_data:
                        continue
                    
                    # Decode base64
                    try:
                        if isinstance(image_data, str):
                            image_bytes = base64.b64decode(image_data)
                        else:
                            image_bytes = image_data
                    except Exception:
                        continue
                    
                    if not image_bytes:
                        continue
                    
                    # Determine file extension
                    ext = 'png'  # default
                    if field_name == 'image_1920' or 'image' in field_name.lower():
                        ext = 'png'
                    elif hasattr(record, '_get_image_extension'):
                        ext = record._get_image_extension(image_bytes) or 'png'
                    
                    # Create file path
                    file_path = f"{self.model_name}/{record.id}/{field_name}.{ext}"
                    
                    # Add to ZIP
                    zip_file.writestr(file_path, image_bytes)
                    
                    # Get external ID
                    external_ids = record.get_external_id()
                    external_id = external_ids.get(record.id, '') or False
                    
                    # Add to mapping
                    mapping.append({
                        'model': self.model_name,
                        'res_id': record.id,
                        'external_id': external_id,
                        'field_name': field_name,
                        'file_path': file_path,
                        'record_name': record_name,
                    })
                    
                    exported_count += 1
                
                # Include attachments if requested
                if self.include_attachments:
                    attachments = self.env['ir.attachment'].search([
                        ('res_model', '=', self.model_name),
                        ('res_id', '=', record.id),
                        ('mimetype', 'like', 'image/%')
                    ])
                    
                    for attachment in attachments:
                        if attachment.datas:
                            try:
                                att_data = base64.b64decode(attachment.datas)
                                att_ext = attachment.mimetype.split('/')[-1] if attachment.mimetype else 'png'
                                att_path = f"{self.model_name}/{record.id}/attachments/{attachment.name or f'attachment_{attachment.id}.{att_ext}'}"
                                
                                zip_file.writestr(att_path, att_data)
                                
                                # Get external ID
                                external_ids = record.get_external_id()
                                external_id = external_ids.get(record.id, '') or False
                                
                                mapping.append({
                                    'model': self.model_name,
                                    'res_id': record.id,
                                    'external_id': external_id,
                                    'field_name': f"attachment_{attachment.id}",
                                    'file_path': att_path,
                                    'record_name': record_name,
                                    'attachment_id': attachment.id,
                                    'attachment_name': attachment.name,
                                })
                                
                                exported_count += 1
                            except Exception:
                                continue
            
            # Add mapping JSON
            zip_file.writestr('mapping.json', json.dumps(mapping, indent=2))
            
            # Add export info
            zip_file.writestr('export_info.json', json.dumps(export_info, indent=2))
        
        # Prepare file for download
        zip_buffer.seek(0)
        zip_data = zip_buffer.read()
        
        filename = f"image_export_{self.model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        self.write({
            'export_file': base64.b64encode(zip_data),
            'filename': filename,
            'state': 'done',
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'image.export.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self._context,
        }
    
    def action_download(self):
        """Return download action for the export file"""
        self.ensure_one()
        if not self.export_file:
            raise UserError(_('No export file available. Please export first.'))
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model=image.export.wizard&id={self.id}&field=export_file&filename_field=filename&download=true',
            'target': 'self',
        }
