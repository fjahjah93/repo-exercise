from odoo import models, fields

class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    def process_cancel_backorder(self):
        # Call the original process_cancel_backorder method
        result = super(StockBackorderConfirmation, self).process_cancel_backorder()

        # Log the activity for "No Backorder is created"
        try:
            task_details = "No Backorder is created."
            
            # Log the activity in user.activity
            self.env['user.activity'].sudo().create({
                'user_id': self.env.user.id,
                'activity_type': 'create',  # Activity type for creation
                'model_name': self._name,
                'record_id': self.id,
                'task_details': task_details,
            })
        except Exception as e:
            # Handle any unexpected errors gracefully
            self.env.cr.rollback()
            self.env['user.activity'].sudo().create({
                'user_id': self.env.user.id,
                'activity_type': 'error',
                'model_name': self._name,
                'record_id': self.id,
                'task_details': f"Error logging activity: {e}",
            })
        
        return result
