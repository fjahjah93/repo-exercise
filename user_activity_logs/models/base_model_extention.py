from odoo import models, api

class BaseModelExtention(models.AbstractModel):
    _inherit = 'base'

    @api.model_create_multi
    def create(self, vals_list):

         # Skip logging for the superuser
        if self.env.user.id == 1:
            return super(BaseModelExtention, self).create(vals_list)
        
        ignored_models = (
            'user.activity', 'bus.bus', 'procurement.group',
            'mail.tracking.value', 'mail.message', 'mail.followers', 'stock.move',
            'stock.quant', 'purchase.order', 'stock.backorder.confirmation',
            'product.template', 'product.product', 'product.supplierinfo', 'product.category', 'stock.picking',
            'hr.expense', 'hr.expense.sheet', 'mail.activity', 'res.partner', 'stock.return.picking',
            'account.full.reconcile',
            'account.partial.reconcile',
            'account.payment.register',
            'account.payment',
            'mail.mail', 'account.account', 'account.journal', 'account.move'
        )

        ignored_fields = [
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
                "type",
                "volume_uom_name",
                "product_variant_ids",
                "product_variant_id",
                "display_name",
                "responsible_id",
                "has_available_route_ids",
                "route_ids",
                "sequence",
                "product_variant_count",
                "last_updated_on",
            ]
        # Skip logging for certain models
        if self._name in ignored_models or self._name.startswith('ir.') or self._name.endswith(('.line', '.layer')):
            return super(BaseModelExtention, self).create(vals_list)

       

        # Create the records
        records = super(BaseModelExtention, self).create(vals_list)

        for record, vals in zip(records, vals_list):
            # Initialize the task_details message
            task_details_lines = [f'Created with the value:']

            # General field logging for common models
            for field_name, field_obj in record._fields.items():

                #Ignor field
                if field_name in ignored_fields:
                        continue
                
                # Fetch field value from vals or the record
                field_value = vals.get(field_name, getattr(record, field_name, None))

                # Check for non-empty values and process them
                if field_value:
                    if field_obj.type in ['many2one']:
                        # For Many2one, fetch the display name
                        value = record[field_name].display_name
                    elif field_obj.type in ['one2many', 'many2many']:
                        # For One2many or Many2many, fetch the count of related records
                        value = f"{len(record[field_name])} related records"
                    else:
                        # For other field types, use the raw value
                        value = field_value

                    # Append field information to task_details_lines
                    task_details_lines.append(f"{field_obj.string}: {value}")

            # Combine all lines into the task_details string
            task_details = "\n".join(task_details_lines)

            # Log the creation activity
            self.env['user.activity'].sudo().create({
                'user_id': self.env.user.id,
                'activity_type': 'create',
                'model_name': self._name,
                'record_id': record.id,
                'task_details': task_details,
            })

        return records
    


    #==================Update Base model======================
    def write(self, vals):
        
        # Skip logging for certain models or specific user
        if self.env.user.id == 1:
           return super(BaseModelExtention, self).write(vals)
        
        ignored_models = (
            'user.activity', 'bus.presence', 'product.template', 'product.product', 'stock.move', 'purchase.order', 'product.category',
            'stock.picking', 'hr.expense', 'hr.expense.sheet', 'mail.activity',
            'account.move', 'account.account', 'account.journal'
        )
        if self._name in ignored_models or self._name.startswith('ir.') or self._name.endswith(('.line', '.layer')):
            return super(BaseModelExtention, self).write(vals)
       
        

        for record in self:
            changes = self._get_field_changes(record, vals)

            exclude_fields = {'group_id', 'tax_country_id', 'needed_terms_dirty', 'move_ids_without_package', }
            
            filtered_changes = {
                field: change for field, change in changes.items() if field not in exclude_fields
            }


            task_details_lines = []

            for field, change in filtered_changes.items():
                field_label = self._fields.get(field).string  # Get the label of the field
                
                
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

        return super(BaseModelExtention, self).write(vals)



    #====================Delete Base model========================
    def unlink(self):

        # Models to ignore for logging
        ignore_models = ('user.activity', 'purchase.order', 'mail.message', 'mail.followers', 'product.template', 'product.category',
                         'mail.activity', 'stock.move', 'account.account', 'account.journal','account.move'
                         )

        # Skip logging for ignored models
        if self._name in ignore_models or self._name.startswith('ir.') or self._name.endswith(('.line', '.layer')):
            return super(BaseModelExtention, self).unlink()

        # Skip logging for superuser
        if self.env.user.id == 1:
            return super(BaseModelExtention, self).unlink()

        for record in self:
            try:
                # Initialize the task_details message
                task_details_lines = [f'"{record.display_name}" has been deleted from model "{self._name}".']

                # General field logging for common models
                for field_name, field_obj in record._fields.items():

                    # Fetch field value
                    field_value = getattr(record, field_name, None)
                    
                    # Check for non-empty values and process them
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
                        
                        # Append field information to task_details_lines
                        task_details_lines.append(f"{field_obj.string}: {value}")

                # Combine all lines into the task_details string
                task_details = "\n".join(task_details_lines)

                # Use display_name for better readability
                record_display_name = record.display_name or "Unknown Record"

                # Log the deletion activity
                self.env['user.activity'].sudo().create({
                    'user_id': self.env.user.id,
                    'activity_type': 'unlink',
                    'model_name': self._name,
                    'record_id': record.id,
                    'record_name': record.id,
                    'task_details': task_details,
                })

            except Exception as e:
                print(f"Error while logging deletion for model {self._name}: {e}")

        # Call the super method to perform the actual deletion
        return super(BaseModelExtention, self).unlink()


    




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



