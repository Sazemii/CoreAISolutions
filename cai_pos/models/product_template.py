# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    """
    Extend Product Template to add BIR discount eligibility configuration.
    
    Per Philippine BIR regulations and RA 9442 (Magna Carta for PWD), 
    RA 9994 (Senior Citizens Act), some items may be excluded from 
    PWD/SC discounts if they are:
    - Already sold at maximum retail price (e.g., medicine with DOH SRP)
    - Excluded by specific regulations
    - Non-essential items per establishment policy
    """
    _inherit = 'product.template'

    # ==========================================
    # VAT-Inclusive Pricing Helper (PH Standard)
    # ==========================================
    # In the Philippines, prices displayed to customers already include VAT.
    # 
    # IMPORTANT: When VAT-inclusive pricing is enabled:
    # - list_price stores the VAT-INCLUSIVE price (e.g., ₱140)
    # - The assigned tax MUST have price_include=True
    # - Odoo's tax engine will compute: base = 140/1.12 = 125, VAT = 15
    # - This is the CORRECT way to handle VAT-inclusive pricing in Odoo
    
    is_vat_inclusive_pricing = fields.Boolean(
        string='VAT-Inclusive Pricing',
        default=True,
        help='Enable this for Philippine standard pricing where the displayed price already includes VAT.\n\n'
             'When enabled:\n'
             '• Enter the customer-facing price (VAT already included)\n'
             '• System will assign VAT 12% (Incl.) tax automatically\n'
             '• The price you enter IS the final price customers pay\n\n'
             'When disabled:\n'
             '• Enter the base price (VAT will be added on top)')
    
    vat_inclusive_price = fields.Float(
        string='VAT-Inclusive Price',
        digits='Product Price',
        compute='_compute_vat_inclusive_price',
        inverse='_inverse_vat_inclusive_price',
        store=False,
        help='Enter the price as displayed to customers (VAT already included).\n'
             'This IS the list_price when VAT-inclusive mode is enabled.\n\n'
             'Example: Enter ₱140, Odoo computes:\n'
             '• Base Price: ₱125.00\n'
             '• VAT (12%): ₱15.00\n'
             '• Total: ₱140.00')
    
    vat_rate_display = fields.Float(
        string='VAT Rate (%)',
        compute='_compute_vat_rate_display',
        help='Current VAT rate from Sales Taxes')
    
    computed_base_price = fields.Float(
        string='Computed Base Price',
        compute='_compute_vat_inclusive_price',
        digits='Product Price',
        help='Base price before VAT (automatically computed from list_price)')
    
    computed_vat_amount = fields.Float(
        string='VAT Amount',
        compute='_compute_vat_inclusive_price',
        digits='Product Price',
        help='VAT amount (automatically computed)')
    
    @api.depends('list_price', 'taxes_id', 'is_vat_inclusive_pricing')
    def _compute_vat_inclusive_price(self):
        """
        Compute VAT breakdown from list_price.
        
        When is_vat_inclusive_pricing=True and tax has price_include=True:
        - list_price IS the VAT-inclusive price
        - We compute the base and VAT for display only
        """
        for product in self:
            list_price = product.list_price
            vat_rate = product._get_vat_rate()
            has_price_include_tax = product._has_price_include_tax()
            
            if product.is_vat_inclusive_pricing and has_price_include_tax and vat_rate > 0:
                # list_price is VAT-inclusive, compute base from it
                # Formula: base = inclusive_price / (1 + rate)
                base_price = list_price / (1 + (vat_rate / 100))
                vat_amount = list_price - base_price
                inclusive_price = list_price
            elif vat_rate > 0 and not has_price_include_tax:
                # list_price is base price, VAT is added on top
                base_price = list_price
                vat_amount = base_price * (vat_rate / 100)
                inclusive_price = base_price + vat_amount
            else:
                # No VAT or no tax configured
                base_price = list_price
                vat_amount = 0.0
                inclusive_price = list_price
            
            product.vat_inclusive_price = inclusive_price
            product.computed_base_price = base_price
            product.computed_vat_amount = vat_amount
    
    def _inverse_vat_inclusive_price(self):
        """
        When user enters VAT-inclusive price, set list_price accordingly.
        
        With price_include=True tax: list_price = inclusive_price (direct assignment)
        Without price_include tax: list_price = inclusive_price / (1 + rate)
        """
        for product in self:
            inclusive_price = product.vat_inclusive_price
            vat_rate = product._get_vat_rate()
            has_price_include_tax = product._has_price_include_tax()
            
            if product.is_vat_inclusive_pricing and has_price_include_tax:
                # Tax has price_include=True, so list_price should be the inclusive price
                product.list_price = inclusive_price
            elif vat_rate > 0:
                # Tax does NOT have price_include, compute base price
                base_price = inclusive_price / (1 + (vat_rate / 100))
                product.list_price = base_price
            else:
                product.list_price = inclusive_price
    
    def _has_price_include_tax(self):
        """Check if any of the sales taxes has price_include=True"""
        self.ensure_one()
        for tax in self.taxes_id:
            if tax.type_tax_use == 'sale' and tax.price_include:
                return True
        return False
    
    @api.onchange('is_vat_inclusive_pricing')
    def _onchange_is_vat_inclusive_pricing(self):
        """
        When VAT-inclusive pricing is enabled, auto-assign the VAT 12% (Incl.) tax.
        This ensures proper tax calculation in Odoo.
        """
        if self.is_vat_inclusive_pricing:
            # Find the VAT 12% (Incl.) tax
            vat_12_incl = self.env['account.tax'].search([
                ('amount', '=', 12.0),
                ('amount_type', '=', 'percent'),
                ('type_tax_use', '=', 'sale'),
                ('price_include', '=', True),
                ('active', '=', True),
            ], limit=1)
            
            if vat_12_incl:
                # Store current list_price as the VAT-inclusive price
                current_price = self.list_price
                
                # Remove any non-price-include taxes and add the price-include one
                self.taxes_id = [(6, 0, [vat_12_incl.id])]
                
                # If we had a price before, keep it (it's now treated as VAT-inclusive)
                if current_price:
                    self.list_price = current_price
    
    @api.depends('taxes_id')
    def _compute_vat_rate_display(self):
        """Get the VAT rate from sales taxes for display"""
        for product in self:
            product.vat_rate_display = product._get_vat_rate()
    
    def _get_vat_rate(self):
        """Get the total VAT rate from sales taxes"""
        self.ensure_one()
        vat_rate = 0.0
        for tax in self.taxes_id:
            if tax.amount_type == 'percent' and tax.type_tax_use == 'sale':
                vat_rate += tax.amount
        return vat_rate

    is_bir_discountable = fields.Boolean(
        string='PWD/SC Discountable',
        default=True,
        help='If checked, this product is eligible for Senior Citizen and PWD discounts.\n\n'
             'Uncheck for items like:\n'
             '• Medicine/medical supplies already at maximum retail price per DOH circular\n'
             '• Items specifically excluded by regulations\n'
             '• Non-essential items per establishment policy\n\n'
             'Note: Most products should remain discountable to comply with RA 9442 and RA 9994.')
    
    bir_discount_exclusion_reason = fields.Char(
        string='Exclusion Reason',
        help='Document why this product is not PWD/SC discountable.\n'
             'Example: "Already at maximum retail price per DOH Circular 2009-0011"')
    
    bir_discountable_notes = fields.Text(
        string='Discount Notes',
        help='Additional notes about discount eligibility for this product')


class ProductProduct(models.Model):
    """
    Extend Product Product to make the field accessible at variant level.
    """
    _inherit = 'product.product'
    
    is_bir_discountable = fields.Boolean(
        related='product_tmpl_id.is_bir_discountable',
        string='PWD/SC Discountable',
        store=True,
        readonly=False,
        help='Whether this product variant is eligible for PWD/SC discounts')
    
    @api.model
    def _load_pos_data_fields(self, config_id):
        """
        Add BIR discount eligibility field to POS data loading.
        This ensures the field is available in the frontend for discount checks.
        """
        fields = super()._load_pos_data_fields(config_id)
        fields.append('is_bir_discountable')
        return fields

