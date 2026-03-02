from odoo import models, api

class AccountJournalExtension(models.Model):
    _inherit = "account.journal"

    @api.model
    def create(self, vals_list):
        try:
            records = super(AccountJournalExtension, self).create(vals_list)

            for record, vals in zip(records, vals_list):
                journal_type_mapping = {
                    "general": "Miscellaneous",
                    "sale": "Sales",
                    "purchase": "Purchase",
                    "bank": "Bank",
                    "cash": "Cash"
                }

                task_details = (
                    f"Journal created.\n"
                    f"Name: {record.name}\n"
                    f"Type: {journal_type_mapping.get(record.type, record.type)}\n"
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
            print(f"Error logging creation for account.journal: {e}")
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

                elif field == "type":
                    task_details_lines.append(f"Type: {change['old']} -> {change['new']}")

                else:
                    task_details_lines.append(f"{field_label}: {change['old']} -> {change['new']}")

            if task_details_lines:
                task_details = "Journal updated.\n" + "\n".join(task_details_lines)

                self.env['user.activity'].sudo().create({
                    'user_id': self.env.user.id,
                    'activity_type': 'write',
                    'model_name': self._name,
                    'record_id': record.id,
                    'task_details': task_details,
                })

        return super(AccountJournalExtension, self).write(vals)

    def unlink(self):
        excluded_fields = [
            "message_follower_ids", "message_ids", "has_message",
            "message_is_follower", "message_partner_ids", "portal_url",
            "access_url", "id", "display_name", "sequence",
            "create_date", "write_date", "company_id", "currency_id",
            "kanban_dashboard", "kanban_dashboard_graph"
        ]

        # Skip logging for superuser (admin)
        if self.env.user.id == 1:
            return super(AccountJournalExtension, self).unlink()

        for record in self:
            try:
                task_details_lines = [f'Journal "{record.name}" has been deleted.']

                # Log important fields explicitly
                task_details_lines.append(f"Journal Type: {record.type}")
             
                # Log other fields dynamically
                for field_name, field_obj in record._fields.items():
                    if field_name in excluded_fields:
                        continue

                    field_value = getattr(record, field_name, None)

                    if field_value:
                        if field_obj.type == "many2one":
                            value = field_value.display_name
                        elif field_obj.type in ["one2many", "many2many"]:
                            value = f"{len(field_value)} related records"
                        else:
                            value = field_value

                        task_details_lines.append(f"{field_obj.string}: {value}")

                # Combine all details
                task_details = "\n".join(task_details_lines)

                # Log the activity
                self.env['user.activity'].sudo().create({
                    'user_id': self.env.user.id,
                    'activity_type': 'unlink',
                    'model_name': self._name,
                    'record_id': record.id,
                    'task_details': task_details,
                })

            except Exception as e:
                print(f"Error while logging deletion for Journal {record.name}: {e}")

        return super(AccountJournalExtension, self).unlink()

    def _get_field_changes(self, record, vals):
        changes = {}
        for field, new_value in vals.items():
            old_value = record[field]
            if old_value != new_value:
                changes[field] = {'old': old_value, 'new': new_value}
        return changes
