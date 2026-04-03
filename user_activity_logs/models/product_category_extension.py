from odoo import models, api, fields

class ProductCategoryExtension(models.Model):
    _inherit = 'product.category'

    @api.model
    def create(self, vals):
        # Call the original create method to create the category
        category = super(ProductCategoryExtension, self).create(vals)
        task_details = (
            f'Product category is created.\n'
            f"Name: {category.name}\n"
            f"Parent Category: {category.parent_id.display_name if category.parent_id else 'None'}\n"
        )

        # Log activity in the user activity model
        self.env['user.activity'].sudo().create({
            'user_id': self.env.user.id,
            'activity_type': 'create',
            'model_name': self._name,
            'record_id': category.id,
            'task_details': task_details,
        })
        return category

    def write(self, vals):

        for record in self:
            changes = self._get_field_changes(record, vals)
            task_details_lines = []

            for field, change in changes.items():
                print("update category")
                field_label = self._fields.get(field).string
                task_details_lines.append(
                    f"{field_label}: {change['old']} -> {change['new']}"
                )

            if task_details_lines:
                task_details = "Product category is updated.\n" + "\n".join(task_details_lines)

                

                self.env['user.activity'].sudo().create({
                    'user_id': self.env.user.id,
                    'activity_type': 'write',
                    'model_name': self._name,
                    'record_id': record.id,
                    'task_details': task_details,
                })

        return super(ProductCategoryExtension, self).write(vals)

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
            "id",
            "display_name",
            "sequence",
            "complete_name",
            "parent_id",
            "parent_path"
        ]
        
        # Skip logging for superuser
        if self.env.user.id == 1:
            return super(ProductCategoryExtension, self).unlink()

        for record in self:
            try:
                # Initialize the task_details message
                task_details_lines = [f'Product category "{record.display_name}" has been deleted.']

                # General field logging for the product.category model
                for field_name, field_obj in record._fields.items():
                    print(f'delete Cat: "{field_name}"')
                    # Ignore excluded fields
                    if field_name in excluded_fields:
                        continue

            

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

                parent_category_name = record.parent_id.display_name if record.parent_id else 'None'
                task_details_lines.append(f'Parent Category: {parent_category_name}')

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
        return super(ProductCategoryExtension, self).unlink()


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
