from odoo import models, fields, api

class UserActivity(models.Model):
    _name = 'user.activity'
    _description = 'User Activity Logs'
    _rec_name = 'record_name'
    _order = 'action_time desc'

    user_id = fields.Many2one('res.users', string="User", required=True)
    activity_type = fields.Selection([
        ('create', 'Create'),
        ('write', 'Update'),
        ('unlink', 'Delete'),
        ('login', 'Login'),
    ], string="Activity Type", required=True)
    model_name = fields.Char(string="Model Name", required=True)
    record_id = fields.Integer(string="Record ID", required=True)
    record_name = fields.Char(string="Record Name", compute="_compute_record_name", store=True)
    action_time = fields.Datetime(string="Action Time", default=fields.Datetime.now)
    task_details = fields.Text(string="Task Details")

    @api.depends('model_name', 'record_id')
    def _compute_record_name(self):
        for record in self:
            try:
                record_model = self.env[record.model_name]
                record_obj = record_model.browse(record.record_id)
                record.record_name = record_obj.display_name if record_obj.exists() else "Record Deleted"
            except KeyError:
                record.record_name = "Invalid Model"
            except Exception:
                record.record_name = "Unknown Record"

    def open_details(self):
        """Handle the details button click."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Details',
            'view_mode': 'form',
            'res_model': 'user.activity',
            'res_id': self.id,
            'target': 'new',  # Open in a popup
            # 'target': 'current',  # Open the form in the main view
        }
    
    def open_record(self):
        """Handle the 'Record' button click to open the related record."""
        if self.record_id and self.model_name:
            return {
                'type': 'ir.actions.act_window',
                'name': f'{self.model_name} Record',
                'view_mode': 'form',
                'res_model': self.model_name,
                'res_id': self.record_id,
                'target': 'current',  # Open in the main view
            }
        else:
            raise print("No associated record found or invalid model.")
