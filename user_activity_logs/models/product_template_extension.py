from odoo import models, api, fields
from datetime import datetime

class ProductTemplateExtension(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        # Call the original create method to create the product
        product = super(ProductTemplateExtension, self).create(vals)
        details = (
            f'Product is created.\n'
            f"Name: {product.name}\n"
            f"Cost Price: {product.standard_price}\n"
            f"Unit of Price: {product.uom_id.name}\n"
        )

        # Log activity in the user activity model
        self.env['user.activity'].sudo().create({
                'user_id': self.env.user.id,
                'activity_type': 'create',
                'model_name': self._name,
                'record_id': product.id,
                'task_details': details,
            })
        # Log the creation of the product

        return product


    #============================Update==============================
    def write(self, vals):
       
        if self.env.user.id == 1:
            return super(ProductTemplateExtension, self).write(vals)

        for record in self:
            changes = self._get_field_changes(record, vals)

            # Exclude fields from logging if necessary
            exclude_fields = {'group_id', 'tax_country_id', 'needed_terms_dirty', 'move_ids_without_package','product_properties'}
            filtered_changes = {
                field: change for field, change in changes.items() if field not in exclude_fields
            }

            task_details_lines = []

            for field, change in filtered_changes.items():
                print(field)
                field_label = self._fields.get(field).string  # Get the label of the field

                if field in ["uom_id", "uom_po_id"]:
                    # Extract old and new UoM IDs
                    old_uom_id = change['old'].id if hasattr(change['old'], '_name') and change['old']._name == 'uom.uom' else change['old']
                    new_uom_id = change['new'].id if hasattr(change['new'], '_name') and change['new']._name == 'uom.uom' else change['new']

                    # Fetch UoM names
                    old_uom_name = self.env['uom.uom'].browse(old_uom_id).name if old_uom_id else "N/A"
                    new_uom_name = self.env['uom.uom'].browse(new_uom_id).name if new_uom_id else "N/A"

                    # Log the changes
                    task_details_lines.append(f"{field_label}: {old_uom_name} -> {new_uom_name}")


                # elif field == "purchase_uom_id":
                #     # Log changes for Unit of Measure and Purchase UoM
                #     old_uom_id = self.env['purchase_uom_id'].browse(change['old']).name if change['old'] else "N/A"
                #     new_uom_id = self.env['purchase_uom_id'].browse(change['new']).name if change['new'] else "N/A"
                #     task_details_lines.append(
                #         f"{field_label}: {old_uom_id} -> {new_uom_id}"
                #     )
                elif field == "list_price":
                    # Log changes in sale price
                    task_details_lines.append(
                        f"{field_label}: {change['old']} -> {change['new']}"
                    )
                elif field == "categ_id":
                    # Log changes in category
                    old_category = record.categ_id.name if record.categ_id else "N/A"
                    new_category = self.env['product.category'].browse(vals.get('categ_id')).name
                    task_details_lines.append(
                        f"Category: {old_category} -> {new_category}"
                    )
                elif field == "type":
                    # Log changes in product type
                    old_type = record.type
                    new_type = vals.get("type")
                    task_details_lines.append(
                        f"Product Type: {old_type} -> {new_type}"
                    )
                elif field == "standard_price":
                    # Log changes in cost price
                    task_details_lines.append(
                        f"Cost Price: {change['old']} -> {change['new']}"
                    )
                elif change['old'] is False:
                    # Log new values when the old value is False
                    task_details_lines.append(
                        f"{field_label}: {change['new']}"
                    )
                else:
                    # General case for logging changes
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

        return super(ProductTemplateExtension, self).write(vals)
    

    #============================Delete=============================
    def unlink(self):
       
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
                "type",
                "volume_uom_name",
                "product_variant_ids",
                "product_variant_id",
                "display_name",
                "responsible_id",
                "has_available_route_ids",
                "route_ids",
                "sequence",
                "product_variant_count"
            ]
        # Skip logging for superuser
        if self.env.user.id == 1:
            return super(ProductTemplateExtension, self).unlink()

        for record in self:
            try:
                # Initialize the task_details message
                task_details_lines = [f'Product "{record.display_name}" has been deleted.']

                # General field logging for common models
                for field_name, field_obj in record._fields.items():
                    
                    #Ignor field
                    if field_name in excluded_fields:
                        continue

                    print(f"delete Field name: {field_name}")

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
        return super(ProductTemplateExtension, self).unlink()
    

    def _get_field_changes(self, record, vals):
        """Utility method to track changes to fields."""
        changes = {}
        for field in vals:
            if field in self._fields:
                old_value = record[field]
                new_value = vals[field]
                if old_value != new_value:
                    changes[field] = {
                        'old': old_value,
                        'new': new_value,
                    }
        return changes

