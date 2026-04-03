from odoo import models, api

class AccountReconciliationExtension(models.Model):
    _inherit = "account.reconcile.model"  # Extend Reconciliation Model

    @api.model
    def create(self, vals_list):
        try:
            records = super(AccountReconciliationExtension, self).create(vals_list)

            for record, vals in zip(records, vals_list):
                task_details = (
                    f"Reconciliation created.\n"
                    f"Name: {record.name}\n"
                    f"Company: {record.company_id.name}\n"
                    f"Type: {record.rule_type or 'N/A'}\n"
                    f"Match Journal: {record.match_journal_ids.mapped('name')}\n"
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
            print(f"Error logging reconciliation creation: {e}")
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

                elif field == "rule_type":
                    task_details_lines.append(f"Rule Type: {change['old']} -> {change['new']}")

                elif field == "match_journal_ids":
                    old_journals = self.env["account.journal"].browse(change["old"]).mapped("name")
                    new_journals = self.env["account.journal"].browse(change["new"]).mapped("name")
                    task_details_lines.append(f"Match Journal: {', '.join(old_journals)} -> {', '.join(new_journals)}")

                else:
                    task_details_lines.append(f"{field_label}: {change['old']} -> {change['new']}")

            if task_details_lines:
                task_details = "Reconciliation updated.\n" + "\n".join(task_details_lines)

                self.env['user.activity'].sudo().create({
                    'user_id': self.env.user.id,
                    'activity_type': 'write',
                    'model_name': self._name,
                    'record_id': record.id,
                    'task_details': task_details,
                })

        return super(AccountReconciliationExtension, self).write(vals)

    def unlink(self):
        for record in self:
            try:
                task_details = (
                    f'Reconciliation "{record.name}" has been deleted.\n'
                    f"Company: {record.company_id.name}\n"
                    f"Rule Type: {record.rule_type or 'N/A'}\n"
                    f"Match Journal: {record.match_journal_ids.mapped('name')}\n"
                )

                self.env['user.activity'].sudo().create({
                    'user_id': self.env.user.id,
                    'activity_type': 'unlink',
                    'model_name': self._name,
                    'record_id': record.id,
                    'task_details': task_details,
                })

            except Exception as e:
                print(f"Error logging reconciliation deletion: {e}")

        return super(AccountReconciliationExtension, self).unlink()

    def _get_field_changes(self, record, vals):
        changes = {}
        for field, new_value in vals.items():
            old_value = record[field]
            if old_value != new_value:
                changes[field] = {'old': old_value, 'new': new_value}
        return changes
