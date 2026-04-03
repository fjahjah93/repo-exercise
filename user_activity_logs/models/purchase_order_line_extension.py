from odoo import models, api, fields
from datetime import datetime


class PurchaseOrderExtension(models.Model):
    _inherit = 'purchase.order'

    #========================Create Purchase order=============================
    @api.model
    def create(self, vals_list):
        print("create purchase module")

        # Skip logging for the superuser
        if self.env.user.id == 1:
            return super(PurchaseOrderExtension, self).create(vals_list)
        
        records = super(PurchaseOrderExtension, self).create(vals_list)

        for record in records:
            vendor_name = record.partner_id.name or "N/A"  # Fetch vendor name
            total_price = record.amount_total  # Fetch total order price
            currency = record.currency_id.name  # Fetch total order price
            tast_details = (
                    f"Purchase order created.\n"
                    f"Order Number: {record.name}\n"
                    f"Vendor: {vendor_name}\n"
                    f"Total Price: {total_price:.2f}{currency}\n"
                )
            self.env['user.activity'].sudo().create({
                'user_id': self.env.user.id,
                'activity_type': 'create',
                'model_name': record._name,
                'record_id': record.id,
                'task_details': tast_details,
            })
        return records
    
    
    #===================Update Purchase order================================

    def write(self, vals):
       
        if self.env.user.id == 1:
            return super(PurchaseOrderExtension, self).write(vals)

        for record in self:

            changes = self._get_field_changes(record, vals)

            exclude_fields = {'group_id', 'tax_country_id', 'needed_terms_dirty', 'move_ids_without_package',}

            filtered_changes = {
                field: change for field, change in changes.items() if field not in exclude_fields
            }


            task_details_lines = []

            for field, change in filtered_changes.items():
                field_label = self._fields.get(field).string  # Get the label of the field
                
                if field == "order_line":
                    # Process changes in order_line
                    task_details_lines.extend(self._process_order_line_changes(change))

                elif field == "currency_id":

                    old_currency = record.currency_id  # `record` represents the current record in the write operation
                    old_currency_name = old_currency and old_currency.exists() and old_currency.name or "N/A"

                    new_currency_id = vals.get("currency_id", False)
                    new_currency = self.env["res.currency"].browse(new_currency_id)
                    new_currency_name = new_currency and new_currency.exists() and new_currency.name or "N/A"


                    # Add the change details to the task details
                    task_details_lines.append(
                        f"{field_label}: {old_currency_name} -> {new_currency_name}"
                    )
                elif field == "partner_id":  # Assuming "partner_id" is the vendor field
                    # Get the old vendor
                    old_vendor = record.partner_id
                    old_vendor_name = old_vendor and old_vendor.exists() and old_vendor.name or "N/A"

                    # Get the new vendor ID from `vals`
                    new_vendor_id = vals.get("partner_id", False)
                    new_vendor = self.env["res.partner"].browse(new_vendor_id)
                    new_vendor_name = new_vendor and new_vendor.exists() and new_vendor.name or "N/A"

                    # Add the change details to the task details
                    task_details_lines.append(
                        f"Vendor: {old_vendor_name} -> {new_vendor_name}"
                    )
                elif field == "date_done":
                    # Special case for 'date_done'
                    purchase_order_number = record.purchase_id.name if record.purchase_id else "N/A"
                    task_details_lines.append(
                       f"The order is Validated.\n"
                       f"Order Number: {purchase_order_number}\n" # Assuming `record.name` contains the order number
                       f"Date of Transfer: {change['new']}"
                    )

                elif field == "state":  # Assuming "partner_id" is the vendor field
                    # Get the old vendor
                    old_state = record.state
                    new_state = vals.get("state")

                    if new_state == "purchase":
                        # Custom message for state transition to 'purchase'
                        task_details_lines.append(
                            f"The order is confirmed.\nState: RFQ -> Purchase Order"
                        )
                    elif new_state == "posted":
                        # Custom message for state transition to 'purchase'
                        vendor_name = record.partner_id.name or "N/A"  # Fetch vendor name
                        total_price = record.amount_total  # Fetch total order price
                        currency = record.currency_id.name  # Fetch total order price
                        task_details_lines.append(
                            f"The Bill is confirmed.\nState: Draft -> Posted\n"
                            f"Invoice Origin: {record.invoice_origin}\n"
                            f"Vendor: {vendor_name}\n"
                            f"Total Price: {total_price:.2f}{currency}"
                        )
                    elif new_state == "cancel":
                        # Custom message for state transition to 'purchase'
                        task_details_lines.append(
                            f"The order has been cancelled.\nState: {old_state} -> Cancel Order"
                        )
                    else:
                        # General message for other state changes
                        task_details_lines.append(
                            f"State: {old_state} -> {new_state}"
                        )

                elif change['old'] is False:
                    # If the old value is False, log only the new value
                    task_details_lines.append(
                        f"{field_label}: {change['new']}"
                    )
                else:
                    # Otherwise, log both the old and new values
                    task_details_lines.append(
                        f"{field}: {change['old']} -> {change['new']}"
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

        return super(PurchaseOrderExtension, self).write(vals)
    

    #==================Delete purchase order=========================
    def unlink(self):
        # Iterate over records to log each purchase order being deleted
        excluded_fields = [
        "message_follower_ids",  # Followers
        "message_ids",           # Messages
        "has_message",           # Messages
        "message_is_follower",   # Is Follower
        "message_partner_ids",   # Followers (Partners)
        "portal_url",            # Portal Access URL
        "access_url",            # Portal Access URL
        "priority",
        "tax_totals",
        "order_line",
        "fiscal_position_id",
        "product_id",
        "id",
        "default_location_dest_id_usage",
        ]
        for record in self:
                try:
                    # Initialize the task_details message
                    task_details_lines = [f'Purchase Order "{record.display_name}" has been deleted.']
                    
                    # Iterate over all fields in the record
                    for field_name, field_obj in record._fields.items():
            
                        if field_name in excluded_fields:
                            continue
                        # Fetch field value
                        field_value = getattr(record, field_name, None)
                        
                        # Check for non-empty values and process them accordingly
                        if field_value:
                            if field_obj.type in ['many2one']:
                                # For Many2one, fetch the display name
                                value = field_value.display_name
                            elif field_obj.type in ['one2many', 'many2many']:
                                # For One2many or Many2many, fetch the count of related records
                                value = f"{len(field_value)} related records"
                            else:
                                # For other field types, use the raw value
                                value = field_value
                            
                            # Append field information to the task_details_lines
                            task_details_lines.append(f"{field_obj.string}: {value}")
                    
                    # Combine all lines into the task_details string
                    # Append product details
                    if record.order_line:
                        product_lines = ["Product Details:"]
                        for line in record.order_line:
                            product_name = line.product_id.display_name
                            quantity = line.product_qty
                            price = line.price_unit
                            product_lines.append(f"- {product_name}, Quantity-{quantity} Price-{price}")
                        task_details_lines.append("\n".join(product_lines))
            
                    task_details = "\n".join(task_details_lines)
                    
                    # Log the deletion activity
                    self.env['user.activity'].sudo().create({
                        'user_id': self.env.user.id,
                        'activity_type': 'unlink',
                        'model_name': self._name,
                        'record_id': record.id,
                        'task_details': task_details,
                    })
                except Exception as e:
                    print(f"Error while logging deletion for model {self._name}: {e}")

        # Call the super method to perform the actual deletion
        return super(PurchaseOrderExtension, self).unlink()
    


    def _get_field_changes(self, record, vals):
        """
        Compare the original values of the fields in `vals` with the new values
        and return the differences as a dictionary.
        """
        changes = {}
        for field, new_value in vals.items():
            old_value = record[field]
            if old_value != new_value:
                changes[field] = {'old': old_value, 'new': new_value}
        return changes

    def _process_order_line_changes(self, changes):
        """
        Process changes in the order_line field and return task details.
        """
        task_details = []
        for line_change in changes['new']:
            if line_change[0] == 1:  # Update operation
                order_line_id = line_change[1]  # ID of the order line
                updated_values = line_change[2]  # Updated values for the line

                product_line = self.env['purchase.order.line'].browse(order_line_id)
                task_details.append("The ordered data has been updated.")

                # Process specific fields
                fields_to_check = {
                    'product_id': 'Product',
                    'name': 'Description',
                    'product_qty': 'Quantity',
                    'price_unit': 'Price',
                    'taxes_id': 'Tax',
                }

                for field_name, label in fields_to_check.items():
                    field_change_detail = self._process_field_change(product_line, field_name, updated_values, label)
                    if field_change_detail:
                        task_details.append(field_change_detail)

        return task_details

    def _process_field_change(self, product_line, field_name, updated_values, label):
        """
        Process a single field change and return the formatted task detail.
        """
        if field_name in updated_values:
            old_value = getattr(product_line, field_name, None)  # Fetch the old value dynamically
            new_value = updated_values[field_name]  # Fetch the new value from updated values
            return f"{product_line.name}:\n{label}: {old_value} -> {new_value}"
        return None

   
