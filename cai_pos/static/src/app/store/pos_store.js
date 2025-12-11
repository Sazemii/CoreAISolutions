/** @odoo-module **/

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { PosOrder } from "@point_of_sale/app/models/pos_order";

// Store BIR discount data separately to avoid conflicts with Odoo's reactive model system
const birDiscountData = new WeakMap();

function getBirData(order) {
    if (!birDiscountData.has(order)) {
        birDiscountData.set(order, {
            discount_type_id: null,
            discount_amount: 0,
            discount_id_number: '',
            discount_id_type: '',
            discountable_gross_sales: 0,
        });
    }
    return birDiscountData.get(order);
}

patch(PosStore.prototype, {
    getBIRDiscountTypes() {
        if (!this.models || !this.models["bir.discount.type"]) {
            return [];
        }
        const birDiscounts = this.models["bir.discount.type"];
        return birDiscounts.getAll ? birDiscounts.getAll() : [];
    },
    
    getBIRConfig() {
        if (!this.models || !this.models["bir.config"]) {
            return null;
        }
        const birConfigModel = this.models["bir.config"];
        const configs = birConfigModel.getAll ? birConfigModel.getAll() : [];
        return configs.length > 0 ? configs[0] : null;
    },
});


patch(PosOrder.prototype, {
    setup(vals) {
        super.setup(...arguments);
        
        // Initialize BIR discount data in separate storage (doesn't interfere with model system)
        const birData = getBirData(this);
        birData.discount_type_id = vals.bir_discount_type_id || null;
        birData.discount_amount = vals.bir_discount_amount || 0;
        birData.discount_id_number = vals.bir_discount_id_number || '';
        birData.discount_id_type = vals.bir_discount_id_type || '';
        birData.discountable_gross_sales = vals.bir_discountable_gross_sales || 0;
    },
    
    // Getter/setter for bir_discount_type_id
    get bir_discount_type_id() {
        return getBirData(this).discount_type_id;
    },
    set bir_discount_type_id(value) {
        getBirData(this).discount_type_id = value;
    },
    
    // Getter/setter for bir_discount_amount
    get bir_discount_amount() {
        return getBirData(this).discount_amount;
    },
    set bir_discount_amount(value) {
        getBirData(this).discount_amount = value;
    },
    
    // Getter/setter for bir_discount_id_number
    get bir_discount_id_number() {
        return getBirData(this).discount_id_number;
    },
    set bir_discount_id_number(value) {
        getBirData(this).discount_id_number = value;
    },
    
    // Getter/setter for bir_discount_id_type
    get bir_discount_id_type() {
        return getBirData(this).discount_id_type;
    },
    set bir_discount_id_type(value) {
        getBirData(this).discount_id_type = value;
    },
    
    // Getter/setter for bir_discountable_gross_sales
    get bir_discountable_gross_sales() {
        return getBirData(this).discountable_gross_sales;
    },
    set bir_discountable_gross_sales(value) {
        getBirData(this).discountable_gross_sales = value;
    },
    
    /**
     * Apply BIR discount to a single NEW line
     */
    applyBIRDiscountToLine(line) {
        const typeId = this.bir_discount_type_id;
        if (!typeId || !this.models) {
            return false;
        }
        
        const birDiscountModel = this.models["bir.discount.type"];
        if (!birDiscountModel) {
            return false;
        }
        
        const discountType = birDiscountModel.get(typeId);
        if (!discountType) {
            return false;
        }
        
        const product = line.get_product ? line.get_product() : line.product_id;
        if (!product) {
            return false;
        }
        
        // Check if product is discountable
        if (product.is_bir_discountable === false) {
            return false;
        }
        
        // Apply discount based on type (VAT-exempt or regular)
        if (discountType.is_vat_exempt) {
            const priceUnit = line.price_unit;
            const priceWithoutVAT = priceUnit / 1.12;
            const finalPrice = priceWithoutVAT * (1 - discountType.discount_percent / 100);
            const effectiveDiscountPercent = ((priceUnit - finalPrice) / priceUnit) * 100;
            
            // Apply VAT-exempt tax if available
            const taxModel = this.models["account.tax"];
            if (taxModel && taxModel.get && discountType.bir_tax_id) {
                const exemptTax = taxModel.get(discountType.bir_tax_id);
                if (exemptTax) {
                    line.tax_ids = [exemptTax];
                }
            }
            
            line.discount = effectiveDiscountPercent;
        } else {
            line.discount = discountType.discount_percent;
        }
        
        return true;
    },
    
    /**
     * Recalculate total BIR discount amount and gross sales from all lines
     */
    recalculateBIRDiscount() {
        try {
            const typeId = this.bir_discount_type_id;
            if (!typeId || !this.models) {
                return;
            }
            
            const birDiscountModel = this.models["bir.discount.type"];
            if (!birDiscountModel) {
                return;
            }
            
            const discountType = birDiscountModel.get(typeId);
            if (!discountType) {
                return;
            }
            
            let totalDiscountAmount = 0;
            let totalGrossSales = 0;
            
            const orderlines = this.get_orderlines ? this.get_orderlines() : [];
            for (const line of orderlines) {
                const product = line.get_product ? line.get_product() : line.product_id;
                if (!product) continue;
                
                if (product.is_bir_discountable === false) {
                    continue;
                }
                
                const prices = line.get_all_prices ? line.get_all_prices() : {};
                
                if (discountType.is_vat_exempt) {
                    const lineDiscountAmount = (prices.priceWithoutTaxBeforeDiscount || 0) - (prices.priceWithoutTax || 0);
                    totalDiscountAmount += lineDiscountAmount;
                    totalGrossSales += prices.priceWithTaxBeforeDiscount || 0;
                } else {
                    const lineDiscountAmount = (prices.priceWithTaxBeforeDiscount || 0) - (prices.priceWithTax || 0);
                    totalDiscountAmount += lineDiscountAmount;
                    totalGrossSales += prices.priceWithTaxBeforeDiscount || 0;
                }
            }
            
            this.bir_discount_amount = totalDiscountAmount;
            this.bir_discountable_gross_sales = totalGrossSales;
        } catch (e) {
            // Silently fail - don't break POS operation
        }
    },
    
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.bir_discount_type_id = this.bir_discount_type_id || false;
        json.bir_discount_amount = this.bir_discount_amount || 0;
        json.bir_discount_id_number = this.bir_discount_id_number || '';
        json.bir_discount_id_type = this.bir_discount_id_type || '';
        json.bir_discountable_gross_sales = this.bir_discountable_gross_sales || 0;
        return json;
    },
    
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.bir_discount_type_id = json.bir_discount_type_id || null;
        this.bir_discount_amount = json.bir_discount_amount || 0;
        this.bir_discount_id_number = json.bir_discount_id_number || '';
        this.bir_discount_id_type = json.bir_discount_id_type || '';
        this.bir_discountable_gross_sales = json.bir_discountable_gross_sales || 0;
    },
    
    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(baseUrl, headerData);
        result.is_reprint = Boolean(this.id);
        
        // Add BIR discount information for printing
        result.bir_discount = null;
        if (this.bir_discount_type_id) {
            const birDiscountModel = this.models ? this.models["bir.discount.type"] : null;
            
            if (birDiscountModel) {
                const discountType = birDiscountModel.get(this.bir_discount_type_id);
                if (discountType) {
                    result.bir_discount = {
                        name: discountType.name,
                        code: discountType.code,
                        percent: discountType.discount_percent,
                        amount: this.bir_discount_amount,
                        id_number: this.bir_discount_id_number,
                        id_type: this.bir_discount_id_type,
                        is_vat_exempt: discountType.is_vat_exempt,
                        discountable_gross_sales: this.bir_discountable_gross_sales,
                    };
                }
            } else {
                result.bir_discount = {
                    name: 'BIR Discount',
                    code: 'DISC',
                    percent: 20,
                    amount: this.bir_discount_amount,
                    id_number: this.bir_discount_id_number,
                    id_type: this.bir_discount_id_type,
                    is_vat_exempt: true,
                    discountable_gross_sales: this.bir_discountable_gross_sales,
                };
            }
        }
        
        // Add BIR config information for printing
        result.bir_config = null;
        const birConfigModel = this.models ? this.models["bir.config"] : null;
        
        if (birConfigModel) {
            const configs = birConfigModel.getAll ? birConfigModel.getAll() : [];
            if (configs.length > 0) {
                const config = configs[0];
                result.bir_config = {
                    business_name: config.business_name,
                    business_address: config.business_address,
                    tin: config.tin,
                    permit_number: config.permit_number,
                    accreditation_number: config.accreditation_number,
                    min_number: config.min_number,
                    serial_number: config.serial_number,
                    terminal_id: config.terminal_id,
                    receipt_prefix: config.receipt_prefix,
                    pos_software_name: config.pos_software_name,
                    pos_software_version: config.pos_software_version,
                };
            }
        }
        
        // Calculate BIR-compliant VAT breakdown
        result.bir_vat_breakdown = this._calculateBIRVATBreakdown(result);
        
        return result;
    },
    
    _calculateBIRVATBreakdown(printData) {
        const breakdown = {
            vatable_sales: 0,
            vat_amount: 0,
            vat_exempt_sales: 0,
            zero_rated_sales: 0,
        };
        
        if (!printData.taxTotals || !printData.taxTotals.subtotals) {
            return breakdown;
        }
        
        const hasVATExemptDiscount = printData.bir_discount && printData.bir_discount.is_vat_exempt;
        
        if (hasVATExemptDiscount) {
            breakdown.vat_exempt_sales = printData.taxTotals.base_amount_currency || 0;
        } else {
            for (const subtotal of printData.taxTotals.subtotals) {
                const taxAmount = subtotal.tax_amount_currency || 0;
                const baseAmount = subtotal.base_amount_currency || 0;
                
                if (taxAmount > 0) {
                    breakdown.vatable_sales += baseAmount;
                    breakdown.vat_amount += taxAmount;
                } else if (baseAmount > 0) {
                    breakdown.zero_rated_sales += baseAmount;
                }
            }
        }
        
        return breakdown;
    },
    
    getBIRDiscount() {
        if (!this.bir_discount_type_id) {
            return null;
        }
        
        if (!this.models || !this.models["bir.discount.type"]) {
            return {
                type: { name: "Unknown Discount", discount_percent: 0 },
                amount: this.bir_discount_amount,
                id_number: this.bir_discount_id_number,
                id_type: this.bir_discount_id_type,
            };
        }
        
        const birDiscountModel = this.models["bir.discount.type"];
        const discountType = birDiscountModel.get(this.bir_discount_type_id);
        
        if (!discountType) {
            return {
                type: { name: "Unknown Discount", discount_percent: 0 },
                amount: this.bir_discount_amount,
                id_number: this.bir_discount_id_number,
                id_type: this.bir_discount_id_type,
            };
        }
        
        return {
            type: discountType,
            amount: this.bir_discount_amount,
            id_number: this.bir_discount_id_number,
            id_type: this.bir_discount_id_type,
        };
    },
    
    hasBIRDiscount() {
        return Boolean(this.bir_discount_type_id);
    },
    
    removeBIRDiscount() {
        if (!this.bir_discount_type_id) {
            return false;
        }
        
        try {
            const orderlines = this.get_orderlines ? this.get_orderlines() : [];
            
            for (const line of orderlines) {
                line.discount = 0;
                if (line.product_id && line.product_id.taxes_id) {
                    line.tax_ids = line.product_id.taxes_id;
                }
            }
            
            this.bir_discount_type_id = null;
            this.bir_discount_amount = 0;
            this.bir_discount_id_number = '';
            this.bir_discount_id_type = '';
            this.bir_discountable_gross_sales = 0;
        } catch (e) {
            // Silently fail
        }
        
        return true;
    },
});
