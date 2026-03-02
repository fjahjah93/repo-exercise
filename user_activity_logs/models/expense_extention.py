from odoo import models, api

class ExpenseExtension(models.Model):
    _inherit = "hr.expense"

    @api.model
    def create(self, vals_list):
        try:
            # Create the records
            records = super(ExpenseExtension, self).create(vals_list)

            for record, vals in zip(records, vals_list):
                task_details = ""

                # Fetch required data for the task details
                expense_name = record.name or "N/A"  # Expense name
                employee_name = record.employee_id.name or "N/A"  # Employee name
                total_price = record.total_amount or 0.0  # Total expense amount
                currency = record.currency_id.name or "N/A"  # Currency

                # Format the task details
                task_details = (
                    f"Expense is created.\n"
                    f"Name: {expense_name}\n"
                    f"Employee: {employee_name}\n"
                    f"Total: {total_price:.2f} {currency}\n"
                )

                # Create a user activity log
                self.env['user.activity'].sudo().create({
                    'user_id': self.env.user.id,
                    'activity_type': 'create',
                    'model_name': self._name,
                    'record_id': record.id,
                    'task_details': task_details,
                })

            return records

        except Exception as e:
            print(f"Error while logging creation for hr.expense: {e}")
            raise




    @api.model
    def write(self, vals):

        # Allow unrestricted updates for admin user
        if self.env.user.id == 1:
            return super(ExpenseExtension, self).write(vals)

        for record in self:
            # Get changes between the current record and the `vals` being updated
            changes = self._get_field_changes(record, vals)

            # Define fields to exclude from logging
            exclude_fields = {'create_date', 'write_date', 'sheet_id', 'message_main_attachment_id'}

            # Filter out excluded fields from changes
            filtered_changes = {
                field: change for field, change in changes.items() if field not in exclude_fields
            }

            task_details_lines = []

            for field, change in filtered_changes.items():
                field_label = self._fields.get(field).string  # Get the label of the field

                if field == "employee_id":
                    # Fetch old and new employee names
                    old_employee = record.employee_id
                    old_employee_name = old_employee and old_employee.exists() and old_employee.name or "N/A"

                    new_employee_id = vals.get("employee_id", False)
                    new_employee = self.env["hr.employee"].browse(new_employee_id)
                    new_employee_name = new_employee and new_employee.exists() and new_employee.name or "N/A"

                    task_details_lines.append(
                        f"{field_label}: {old_employee_name} -> {new_employee_name}"
                    )

                elif field == "total_amount":
                    # Log changes in the total expense amount
                    task_details_lines.append(
                        f"{field_label}: {change['old']:.2f} -> {change['new']:.2f}"
                    )
                # elif field == "sheet_id":
                #     # Log changes in the total expense amount
                #     task_details_lines.append(
                #          f"The expense report is created."
                #     )

                elif field == "state":
                    # Log state transitions with custom messages
                    old_state = record.state
                    new_state = vals.get("state")
                    
                    if new_state == "done":
                        task_details_lines.append(
                            f"The expense has been approved.\nState: {old_state} -> Approved"
                        )
                    elif new_state == "cancel":
                        task_details_lines.append(
                            f"The expense has been cancelled.\nState: {old_state} -> Cancelled"
                        )
                    else:
                        task_details_lines.append(
                            f"State: {old_state} -> {new_state}"
                        )

                elif field == "currency_id":
                    # Log changes in the currency
                    old_currency = record.currency_id
                    old_currency_name = old_currency and old_currency.exists() and old_currency.name or "N/A"

                    new_currency_id = vals.get("currency_id", False)
                    new_currency = self.env["res.currency"].browse(new_currency_id)
                    new_currency_name = new_currency and new_currency.exists() and new_currency.name or "N/A"

                    task_details_lines.append(
                        f"{field_label}: {old_currency_name} -> {new_currency_name}"
                    )

                elif change['old'] is False:
                    # If the old value is False, log only the new value
                    task_details_lines.append(
                        f"{field_label}: {change['new']}"
                    )

                else:
                    # General logging for all other fields
                    task_details_lines.append(
                        f"{field}: {change['old']} -> {change['new']}"
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

        return super(ExpenseExtension, self).write(vals)
    

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

    def action_submit_expenses(self):
        # Call the original process_cancel_backorder method
        result = super(ExpenseExtension, self).action_submit_expenses()

        # Log the activity for "No Backorder is created"
       
        task_details = "The expense report is created."
            
            # Log the activity in user.activity
        self.env['user.activity'].sudo().create({
                'user_id': self.env.user.id,
                'activity_type': 'create',  # Activity type for creation
                'model_name': self._name,
                'record_id': self.id,
                'task_details': task_details,
            })
        return result
