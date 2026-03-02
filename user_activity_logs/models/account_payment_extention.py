from odoo import models, api, _

import logging
_logger = logging.getLogger(__name__)

class AccountPaymentExtension(models.Model):
    _inherit = 'account.payment'

    @api.model
    def create(self, vals):
        # Call the super method to create the payment record
        payment = super(AccountPaymentExtension, self).create(vals)

        try:
            # Fetch related information
            employee_name = payment.create_uid.name or "N/A"  # Employee who created the payment
            amount = payment.amount or 0.0  # Payment amount
            currency = payment.currency_id.name or "N/A"  # Currency name

            task_details = (
                f"Payment is registered.\n"
                f"Employee: {employee_name}\n"
                f"Amount: {amount} {currency}\n"
            )

            # Log the activity in the `user.activity` model
            self.env['user.activity'].sudo().create({
                'user_id': self.env.user.id,
                'activity_type': 'create',
                'model_name': payment._name,
                'record_id': payment.id,
                'record_name': payment.display_name,  # Store the readable name
                'task_details': task_details,
            })
        except Exception as e:
            _logger.error(f"Failed to log activity for Account Payment: {e}")

        return payment
