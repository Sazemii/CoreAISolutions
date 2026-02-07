# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import float_round

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

    @api.model
    def default_get(self, fields_list):
        """Set default Sales Tax to VAT 12%"""
        res = super().default_get(fields_list)
        if 'taxes_id' in fields_list:
            # Find VAT 12% tax (regular, not included)
            vat_12 = self.env['account.tax'].search([
                ('amount', '=', 12.0),
                ('amount_type', '=', 'percent'),
                ('type_tax_use', '=', 'sale'),
                ('price_include', '=', False),
                ('active', '=', True),
            ], limit=1)
            if vat_12:
                res['taxes_id'] = [(6, 0, [vat_12.id])]
        return res

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
                base_price = float_round(list_price / (1 + (vat_rate / 100)), precision_digits=2)
                vat_amount = float_round(list_price - base_price, precision_digits=2)
                inclusive_price = list_price
            elif vat_rate > 0 and not has_price_include_tax:
                # list_price is base price, VAT is added on top
                base_price = list_price
                vat_amount = float_round(base_price * (vat_rate / 100), precision_digits=2)
                inclusive_price = float_round(base_price + vat_amount, precision_digits=2)
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
        
        IMPORTANT: For VAT-inclusive pricing with price_include=True, we adjust the list_price
        to ensure that when Odoo computes base = list_price / (1 + rate) and then 
        total = base * (1 + rate), we get exactly the desired inclusive price.
        This prevents rounding errors in POS calculations.
        """
        for product in self:
            inclusive_price = product.vat_inclusive_price
            vat_rate = product._get_vat_rate()
            has_price_include_tax = product._has_price_include_tax()
            
            if product.is_vat_inclusive_pricing and has_price_include_tax and vat_rate > 0:
                # Tax has price_include=True
                # To avoid rounding errors in POS, we store a price that when divided by (1 + rate)
                # gives a rounded base that reconstructs to the desired inclusive price.
                # 
                # Strategy: 
                # 1. Compute rounded base from desired inclusive price
                # 2. Compute what list_price should be to produce that rounded base
                # 3. Store the exact adjusted price (without rounding) so that when Odoo's tax engine
                #    divides by (1 + rate), it gets the rounded base, which then reconstructs correctly
                base_price = float_round(inclusive_price / (1 + (vat_rate / 100)), precision_digits=2)
                # Compute list_price that produces this rounded base
                # Store the exact value (e.g., 74.9952) so division by 1.12 gives exactly 66.96
                # The field's digits parameter will handle display rounding, but the stored value
                # ensures correct tax computation
                adjusted_list_price = base_price * (1 + (vat_rate / 100))
                # Store without rounding to preserve precision for tax computation
                # The digits='Product Price' on the field will handle display formatting
                product.list_price = adjusted_list_price
            elif vat_rate > 0:
                # Tax does NOT have price_include, compute base price
                base_price = float_round(inclusive_price / (1 + (vat_rate / 100)), precision_digits=2)
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
        VAT-inclusive pricing mode changed.
        Note: Tax assignment is now manual - user selects the appropriate tax.
        """
        # No auto-assignment - user manually selects tax
        pass
    
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
    Also add VAT-inclusive pricing support at variant level.
    """
    _inherit = 'product.product'
    
    is_bir_discountable = fields.Boolean(
        related='product_tmpl_id.is_bir_discountable',
        string='PWD/SC Discountable',
        store=True,
        readonly=False,
        help='Whether this product variant is eligible for PWD/SC discounts')
    
    # VAT-Inclusive Pricing at Variant Level
    # Inherit the flag from template, but allow variant-level override
    is_vat_inclusive_pricing = fields.Boolean(
        related='product_tmpl_id.is_vat_inclusive_pricing',
        string='VAT-Inclusive Pricing',
        readonly=True,
        help='VAT-inclusive pricing mode (inherited from template)')
    
    vat_inclusive_price = fields.Float(
        string='VAT-Inclusive Price',
        digits='Product Price',
        compute='_compute_vat_inclusive_price_variant',
        inverse='_inverse_vat_inclusive_price_variant',
        store=False,
        help='Enter the price as displayed to customers (VAT already included).\n'
             'This works with lst_price when VAT-inclusive mode is enabled.')
    
    vat_rate_display = fields.Float(
        string='VAT Rate (%)',
        compute='_compute_vat_rate_display_variant',
        help='Current VAT rate from Sales Taxes')
    
    computed_base_price = fields.Float(
        string='Computed Base Price',
        compute='_compute_vat_inclusive_price_variant',
        digits='Product Price',
        help='Base price before VAT (automatically computed from lst_price)')
    
    computed_vat_amount = fields.Float(
        string='VAT Amount',
        compute='_compute_vat_inclusive_price_variant',
        digits='Product Price',
        help='VAT amount (automatically computed)')
    
    @api.depends('lst_price', 'taxes_id', 'is_vat_inclusive_pricing', 'list_price', 'price_extra')
    def _compute_vat_inclusive_price_variant(self):
        """
        Compute VAT breakdown from lst_price (variant-level price).
        
        When is_vat_inclusive_pricing=True and tax has price_include=True:
        - lst_price IS the VAT-inclusive price
        - We compute the base and VAT for display only
        """
        for product in self:
            lst_price = product.lst_price
            vat_rate = product._get_vat_rate_variant()
            has_price_include_tax = product._has_price_include_tax_variant()
            
            if product.is_vat_inclusive_pricing and has_price_include_tax and vat_rate > 0:
                # lst_price is VAT-inclusive, compute base from it
                # Formula: base = inclusive_price / (1 + rate)
                base_price = float_round(lst_price / (1 + (vat_rate / 100)), precision_digits=2)
                vat_amount = float_round(lst_price - base_price, precision_digits=2)
                inclusive_price = lst_price
            elif vat_rate > 0 and not has_price_include_tax:
                # lst_price is base price, VAT is added on top
                base_price = lst_price
                vat_amount = float_round(base_price * (vat_rate / 100), precision_digits=2)
                inclusive_price = float_round(base_price + vat_amount, precision_digits=2)
            else:
                # No VAT or no tax configured
                base_price = lst_price
                vat_amount = 0.0
                inclusive_price = lst_price
            
            product.vat_inclusive_price = inclusive_price
            product.computed_base_price = base_price
            product.computed_vat_amount = vat_amount
    
    def _inverse_vat_inclusive_price_variant(self):
        """
        When user enters VAT-inclusive price for variant, set lst_price accordingly.
        
        This will trigger the existing _set_product_lst_price inverse method which
        updates the template's list_price. However, since each variant can have different
        price_extra values, the effective lst_price will be different per variant.
        
        Note: In Odoo, variants share the template's list_price but can have different
        price_extra values through attribute values. For completely independent prices,
        users should set price_extra on the variant's attribute values.
        
        IMPORTANT: For VAT-inclusive pricing with price_include=True, we adjust the lst_price
        to ensure proper rounding consistency (same logic as template level).
        """
        for product in self:
            inclusive_price = product.vat_inclusive_price
            vat_rate = product._get_vat_rate_variant()
            has_price_include_tax = product._has_price_include_tax_variant()
            
            if product.is_vat_inclusive_pricing and has_price_include_tax and vat_rate > 0:
                # Tax has price_include=True
                # Use same rounding strategy as template to ensure consistency
                base_price = float_round(inclusive_price / (1 + (vat_rate / 100)), precision_digits=2)
                # Compute lst_price that produces this rounded base
                # Store the exact value without rounding to preserve precision for tax computation
                adjusted_lst_price = base_price * (1 + (vat_rate / 100))
                product.lst_price = adjusted_lst_price
            elif vat_rate > 0:
                # Tax does NOT have price_include, compute base price first
                # The inclusive_price includes VAT, so we need the base
                base_price = float_round(inclusive_price / (1 + (vat_rate / 100)), precision_digits=2)
                # lst_price should be the base (VAT will be added by tax computation)
                product.lst_price = base_price
            else:
                # No VAT, lst_price = inclusive_price
                product.lst_price = inclusive_price
    
    def _has_price_include_tax_variant(self):
        """Check if any of the sales taxes has price_include=True"""
        self.ensure_one()
        for tax in self.taxes_id:
            if tax.type_tax_use == 'sale' and tax.price_include:
                return True
        return False
    
    @api.depends('taxes_id')
    def _compute_vat_rate_display_variant(self):
        """Get the VAT rate from sales taxes for display"""
        for product in self:
            product.vat_rate_display = product._get_vat_rate_variant()
    
    def _get_vat_rate_variant(self):
        """Get the total VAT rate from sales taxes"""
        self.ensure_one()
        vat_rate = 0.0
        for tax in self.taxes_id:
            if tax.amount_type == 'percent' and tax.type_tax_use == 'sale':
                vat_rate += tax.amount
        return vat_rate
    
    @api.model
    def _load_pos_data_fields(self, config_id):
        """
        Add BIR discount eligibility field to POS data loading.
        This ensures the field is available in the frontend for discount checks.
        """
        fields = super()._load_pos_data_fields(config_id)
        fields.append('is_bir_discountable')
        return fields

