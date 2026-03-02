from odoo import models, api

class PartnerExtension(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        # Call the original create method to create the vendor
        vendor = super(PartnerExtension, self).create(vals)
        details = (
            f'Vendor is created.\n'
            f"Vendor Name: {vendor.name}\n"
            f"Mobile: {vendor.mobile or 'N/A'}\n"
        )

        # Log activity in the user activity model
        self.env['user.activity'].sudo().create({
            'user_id': self.env.user.id,
            'activity_type': 'create',
            'model_name': self._name,
            'record_id': vendor.id,
            'task_details': details,
        })

        return vendor
