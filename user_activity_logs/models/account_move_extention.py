from odoo import models, api

class AccountMoveExtension(models.Model):
    _inherit = "account.move"

    @api.model
    def create(self, vals_list):
        try:
            records = super(AccountMoveExtension, self).create(vals_list)

            for record, vals in zip(records, vals_list):
                task_details = ""

                if record.move_type == "in_invoice":  # Vendor Bill
                    vendor_name = record.partner_id.name or "N/A"
                    total_price = record.amount_total
                    currency = record.currency_id.name
                    invoice_origin = record.invoice_origin or "N/A"
                    task_details = (
                        f"Vendor bill has been created.\n"
                        f"Invoice Origin: {invoice_origin}\n"
                        f"Vendor: {vendor_name}\n"
                        f"Total Price: {total_price:.2f} {currency}\n"
                    )
                else:  # General logging for other journal entries
                    task_details = (
                        f"Journal Entry created.\n"
                        f"Reference: {record.ref}\n"
                        f"Journal: {record.journal_id.display_name}\n"
                        f"Type: {record.move_type}\n"
                        f"Total Amount: {record.amount_total} {record.currency_id.name}\n"
                        f"Status: {record.state}"
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
            print(f"Error logging creation for account.move: {e}")
            raise

    def write(self, vals):
        for record in self:
            changes = self._get_field_changes(record, vals)

            exclude_fields = {'create_date', 'write_date', 'tax_country_id', 'is_manually_modified', 'checked'}
            filtered_changes = {
                field: change for field, change in changes.items() if field not in exclude_fields
            }

            task_details_lines = []

            for field, change in filtered_changes.items():
                if field in exclude_fields:
                    continue

                field_label = self._fields.get(field).string

                if field == "journal_id":
                    old_journal = self.env["account.journal"].browse(change["old"])
                    new_journal = self.env["account.journal"].browse(change["new"])
                    task_details_lines.append(f"Journal: {old_journal.display_name or 'N/A'} -> {new_journal.display_name or 'N/A'}")

                elif field == "currency_id":
                    old_currency = self.env["res.currency"].browse(change["old"])
                    new_currency = self.env["res.currency"].browse(change["new"])
                    task_details_lines.append(f"Currency: {old_currency.name or 'N/A'} -> {new_currency.name or 'N/A'}")

                elif field == "state":
                    task_details_lines.append(f"Status: {change['old']} -> {change['new']}")

                elif field == "amount_total":
                    task_details_lines.append(f"Total Amount: {change['old']} -> {change['new']} {record.currency_id.name}")

                else:
                    task_details_lines.append(f"{field_label}: {change['old']} -> {change['new']}")

            if task_details_lines:
                task_details = "Journal Entry updated.\n" + "\n".join(task_details_lines)

                self.env['user.activity'].sudo().create({
                    'user_id': self.env.user.id,
                    'activity_type': 'write',
                    'model_name': self._name,
                    'record_id': record.id,
                    'task_details': task_details,
                })

        return super(AccountMoveExtension, self).write(vals)

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
            return super(AccountMoveExtension, self).unlink()

        for record in self:
            try:
                task_details_lines = [f'Journal Entry "{record.name}" has been deleted.']

                # Log important fields explicitly
                task_details_lines.append(f"Journal: {record.journal_id.display_name}")
                task_details_lines.append(f"Total Amount: {record.amount_total} {record.currency_id.name}")
                task_details_lines.append(f"Status: {record.state}")

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
                print(f"Error while logging deletion for Journal Entry {record.name}: {e}")

        return super(AccountMoveExtension, self).unlink()

    def _get_field_changes(self, record, vals):
        changes = {}
        for field, new_value in vals.items():
            old_value = record[field]
            if old_value != new_value:
                changes[field] = {'old': old_value, 'new': new_value}
        return changes
