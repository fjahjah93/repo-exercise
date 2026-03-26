from odoo import models, fields, api

class StockPickingExtension(models.Model):
    _inherit = 'stock.picking'

    #========================Create Stock picking=============================
    @api.model
    def create(self, vals_list):
        # Skip logging for the superuser
        if self.env.user.id == 1:
            return super(StockPickingExtension, self).create(vals_list)
        
        # Call the super method to create the stock picking records
        records = super(StockPickingExtension, self).create(vals_list)

        # Log details for each created record
        for record in records:
            vendor_name = record.partner_id.name or "N/A"  # Vendor name
            picking_type = record.picking_type_id.name or "N/A"  # Picking type
            source_location = record.location_id.display_name or "N/A"  # Source location
            destination_location = record.location_dest_id.display_name or "N/A"  # Destination location

            # Check if the picking type is internal transfer
            if record.picking_type_id.code == 'internal':
                task_details = (
                    f"Internal transfer is created.\n"
                    f"Contact: {vendor_name}\n"
                    f"Source Location: {source_location}\n"
                    f"Destination Location: {destination_location}\n"
                )
            else:
                task_details = (
                    f"Product transfer created.\n"
                    f"Contact: {vendor_name}\n"
                    f"Picking Type: {picking_type}\n"
                    f"Source Location: {source_location}\n"
                    f"Destination Location: {destination_location}\n"
                )

            # Log the activity in the `user.activity` model
            self.env['user.activity'].sudo().create({
                'user_id': self.env.user.id,
                'activity_type': 'create',
                'model_name': record._name,
                'record_id': record.id,
                'task_details': task_details,
            })

        return records

    

    #=================Update Stock picking=======================
    def write(self, vals):

        for record in self:
            changes = self._get_field_changes(record, vals)
            print(f'{record}')

            exclude_fields = {'group_id', 'tax_country_id', 'needed_terms_dirty', 'move_ids_without_package',
                              'contact','partner_id', }
            
            filtered_changes = {
                field: change for field, change in changes.items() if field not in exclude_fields
            }


            task_details_lines = []

            for field, change in filtered_changes.items():
                print(f'change field: {field}')
                field_label = self._fields.get(field).string  # Get the label of the field
                
                if record.picking_type_id.code == 'internal' and field == "date_done":
                    # Special case for 'date_done'
                    vendor_name = record.partner_id.name or "N/A" 
                    source_location = record.location_id.display_name or "N/A"  # Source location
                    destination_location = record.location_dest_id.display_name or "N/A"  # Destination location
                    task_details_lines.append(
                       f"Internal Transfer is validated.\n"
                       f"Contact: {vendor_name}\n" # Assuming `record.name` contains the order number
                       f"Source Location: {source_location}\n"
                       f"Destination Location: {destination_location}\n"
                    )
                elif field == "date_done":
                    # Special case for 'date_done'
                    purchase_order_number = record.purchase_id.name if record.purchase_id else "N/A"
                    task_details_lines.append(
                       f"The order is validated.\n"
                       f"Order Number: {purchase_order_number}\n" # Assuming `record.name` contains the order number                
                    )

                elif field == 'move_ids_without_package':
                    move_ids = record.move_ids_without_package.browse(change[1])
                    if not move_ids:
                        continue
                    for move in move_ids:
                        old_quantity = move.product_uom_qty
                        new_quantity = changes['quantity']
                        task_details_lines.append(
                                f"The received quantity has been changed.\n"
                                f"Quantity: {old_quantity} -> {new_quantity}"
                        )


                else:
                 # Otherwise, log both the old and new values
                    task_details_lines.append(
                        f"{field_label}: {change['old']} -> {change['new']}"
                    )
            

            if task_details_lines:  # Only log if there are meaningful changes
                task_details = "\n".join(task_details_lines)

                self.env['user.activity'].sudo().create({
                    'user_id': self.env.user.id,
                    'activity_type': 'write',
                    'model_name': self._name,
                    'record_id': record.id,
                    'task_details': f"{task_details}",
                })


        # Call the super method to ensure standard functionality
        return super(StockPickingExtension, self).write(vals)



    def action_confirm(self):
        # Custom logic before the original method
        for picking in self:
            print(f"Mark as Todo clicked for Picking: {picking.name}")

            # Log the activity in the `user.activity` model
            self.env['user.activity'].sudo().create({
                'user_id': self.env.user.id,
                'activity_type': 'write',
                'model_name': picking._name,
                'record_id': picking.id,
                'task_details': f"Marked as Todo is created.",
            })

        # Call the original method
        result = super(StockPickingExtension, self).action_confirm()

        return result