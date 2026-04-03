from odoo import models, api

class ExpenseSheetExtension(models.Model):
    _inherit = "hr.expense.sheet"


    @api.model
    def write(self, vals):

        # Allow unrestricted updates for admin user
        if self.env.user.id == 1:
            return super(ExpenseSheetExtension, self).write(vals)

        for record in self:
            # Get changes between the current record and the `vals` being updated
            changes = self._get_field_changes(record, vals)

            # Define fields to exclude from logging
            exclude_fields = {'create_date', 'write_date', 'sheet_id', 'message_main_attachment_id', 'user_id', 'department_id'}

            # Filter out excluded fields from changes
            filtered_changes = {
                field: change for field, change in changes.items() if field not in exclude_fields
            }

            task_details_lines = []

            for field, change in filtered_changes.items():
                field_label = self._fields.get(field).string  # Get the label of the field


                if field == "approval_state":
                    # Log state transitions with custom messages
                    old_state = record.state
                    new_state = vals.get("approval_state")
                    
                    if new_state == "approve":
                        employee_name = record.employee_id.name or "N/A"  # Fetch employee name
                        total_price = record.total_amount  # Fetch total expense amount
                        currency = record.currency_id.name or "N/A"  # Fetch currency
                        task_details_lines.append(
                            f"The expense has been approved.\n"
                            f"State: {old_state} -> Approved\n"
                            f"Employee: {employee_name}\n"
                            f"Total: {total_price:.2f} {currency}"
                        )
                    elif new_state == "submit":
                        task_details_lines.append(
                            f"The expense is submited."
                        )
                    else:
                        task_details_lines.append(
                            f"State: {old_state} -> {new_state}"
                        )

                elif change['old'] is False:
                    # If the old value is False, log only the new value
                    task_details_lines.append(
                        f"{field_label}: {change['new']}"
                    )

                else:
                    # General logging for all other fields
                    task_details_lines.append(
                        f"{field_label}: {change['old']} -> {change['new']}"
                    )

            # Log the changes if any meaningful changes exist
            if task_details_lines:
                task_details = "\n".join(task_details_lines)

                self.env['user.activity'].sudo().create({
                    'user_id': self.env.user.id,
                    'activity_type': 'write',
                    'model_name': self._name,
                    'record_id': record.id,
                    'task_details': f"{task_details}",
                })

        return super(ExpenseSheetExtension, self).write(vals)
    

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

