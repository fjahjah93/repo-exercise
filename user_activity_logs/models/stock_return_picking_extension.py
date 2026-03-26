from odoo import models, api, _

import logging
_logger = logging.getLogger(__name__)

class StockReturnPickingExtension(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.model
    def create(self, vals_list):
        # Ensure vals_list is a list
        vals_list = [vals_list] if isinstance(vals_list, dict) else vals_list

        # Call the super method to create records
        records = super(StockReturnPickingExtension, self).create(vals_list)

        for record in records:
            try:
                # Fetch associated picking
                original_picking = self.env['stock.picking'].browse(record.picking_id.id)
                vendor_name = original_picking.partner_id.name or "N/A"
                picking_type = original_picking.picking_type_id.name or "N/A"
                source_location = original_picking.location_id.display_name or "N/A"
                destination_location = original_picking.location_dest_id.display_name or "N/A"

            
                # Check if the picking type is internal transfer
                if original_picking.picking_type_id.code == 'internal':
                    task_details = (
                        f"Product returned from internal transfer.\n"
                        f"Contact: {vendor_name}\n"
                        f"Source Location: {destination_location}\n"
                        f"Destination Location: {source_location}\n"
                    )
                else:
                    task_details = (
                        f"Product return created.\n"
                        f"Contact: {vendor_name}\n"
                        f"Picking Type: {picking_type}\n"
                        f"Source Location: {destination_location}\n"
                        f"Destination Location: {source_location}\n"
                    )

                # Use display_name for better readability
                record_display_name = record.display_name or "Unknown Record"

                # Log the activity in the `user.activity` model
                self.env['user.activity'].sudo().create({
                    'user_id': self.env.user.id,
                    'activity_type': 'create',
                    'model_name': record._name,
                    'record_id': record.id,
                    'record_name': record_display_name,
                    'task_details': task_details,
                })
            except Exception as e:
                _logger.error(f"Failed to log activity for Stock Return Picking: {e}")
        return records
