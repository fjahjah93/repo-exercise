from odoo import models, api

class AccountAccountExtension(models.Model):
    _inherit = "account.account"

    @api.model
    def create(self, vals_list):
        try:
            records = super(AccountAccountExtension, self).create(vals_list)

            for record, vals in zip(records, vals_list):
                account_type_mapping = {
                    'asset_current': 'Current Asset',
                    'liability_current': 'Current Liability',
                    'income': 'Income',
                    'expense': 'Expense',
                    # Add more mappings if needed
                }

                task_details = (
                    f"Chart of Account created.\n"
                    f"Name: {record.name}\n"
                    f"Code: {record.code}\n"
                    f"Account Type: {account_type_mapping.get(record.account_type, record.account_type)}\n"
                )

                self.env['user.activity'].sudo().create({
                    'user_id': self.env.user.id,
                    'activity_type': 'create',
                    'model_name': self._name,
                    'record_id': record.id,
                    'task_details': task_details,
                })

            return records
        except Exception as e:
            print(f"Error logging creation for account.account: {e}")
            raise

    def write(self, vals):
        for record in self:
            changes = self._get_field_changes(record, vals)

            exclude_fields = {'create_date', 'write_date'}
            filtered_changes = {
                field: change for field, change in changes.items() if field not in exclude_fields
            }

            task_details_lines = []

            for field, change in filtered_changes.items():
                field_label = self._fields.get(field).string

                if field == "company_id":
                    old_company = self.env["res.company"].browse(change["old"])
                    new_company = self.env["res.company"].browse(change["new"])
                    task_details_lines.append(f"Company: {old_company.name or 'N/A'} -> {new_company.name or 'N/A'}")

                elif field == "account_type":
                    task_details_lines.append(f"Account Type: {change['old']} -> {change['new']}")

                else:
                    task_details_lines.append(f"{field_label}: {change['old']} -> {change['new']}")

            if task_details_lines:
                task_details = "Chart of account updated.\n" + "\n".join(task_details_lines)

                self.env['user.activity'].sudo().create({
                    'user_id': self.env.user.id,
                    'activity_type': 'write',
                    'model_name': self._name,
                    'record_id': record.id,
                    'task_details': task_details,
                })

        return super(AccountAccountExtension, self).write(vals)

    def unlink(self):
        for record in self:
            task_details = f"Chart of Account {record.name} (Code: {record.code}) has been deleted."

            self.env['user.activity'].sudo().create({
                'user_id': self.env.user.id,
                'activity_type': 'unlink',
                'model_name': self._name,
                'record_id': record.id,
                'task_details': task_details,
            })

        return super(AccountAccountExtension, self).unlink()

    def _get_field_changes(self, record, vals):
        changes = {}
        for field, new_value in vals.items():
            old_value = record[field]
            if old_value != new_value:
                changes[field] = {'old': old_value, 'new': new_value}
        return changes
