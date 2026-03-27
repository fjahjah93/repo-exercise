# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sub_id = fields.Char(
        string='Platform ID',
        help='External platform identifier (Sub ID)',
        copy=False,
        index=True
    )
    
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string='Gender')
    
    contact_type = fields.Selection([
        ('driver', 'Driver'),
        ('rider', 'Rider'),
    ], string='Contact Type')
     

    billing_type = fields.Selection([
        ('commission', 'Commission'),
        ('subscription', 'Subscription'),
    ], string='Billing Type')

    def _caram_apply_accounting_partner_accounts(self):
        """Set company-dependent AR/AP from CarAm settings when role is rider or driver."""
        for partner in self:
            company = partner.env.company
            if not company:
                continue
        
            role = partner.contact_type
            if not role:
                continue
            if role == 'rider':
                receivable = company.caram_rider_receivable_account_id
                payable = company.caram_rider_payable_account_id
                
            elif role == 'driver':
                receivable = company.caram_driver_receivable_account_id
                payable = company.caram_driver_payable_account_id
            if not receivable or not payable:
                continue

            partner.with_company(company).write({
                'property_account_receivable_id': receivable.id,
                'property_account_payable_id': payable.id,
            })

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        partners._caram_apply_accounting_partner_accounts()
        return partners

    
    @api.constrains('sub_id', 'company_id')
    def _check_unique_sub_id(self):
        """Ensure sub_id is unique per company"""
        for record in self:
            if record.sub_id and record.company_id:
                existing = self.search([
                    ('sub_id', '=', record.sub_id),
                    ('company_id', '=', record.company_id.id),
                    ('id', '!=', record.id)
                ], limit=1)
                if existing:
                    raise ValidationError(
                        f"A contact with Platform ID '{record.sub_id}' already exists in this company."
                    )

