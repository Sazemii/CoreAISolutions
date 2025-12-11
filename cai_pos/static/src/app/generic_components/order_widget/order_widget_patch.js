/** @odoo-module **/

import { OrderWidget } from "@point_of_sale/app/generic_components/order_widget/order_widget";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";

/**
 * Patch OrderWidget to display BIR discount calculations in the order summary
 */
patch(OrderWidget.prototype, {
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
    },
    
    /**
     * Get the current order for accessing BIR discount info
     */
    get currentOrder() {
        return this.pos?.get_order();
    },
    
    /**
     * Check if current order has a BIR discount applied
     */
    get hasBIRDiscount() {
        const order = this.currentOrder;
        return order && order.hasBIRDiscount && order.hasBIRDiscount();
    },
    
    /**
     * Get BIR discount details for display
     */
    get birDiscountInfo() {
        const order = this.currentOrder;
        if (!order || !order.hasBIRDiscount || !order.hasBIRDiscount()) {
            return null;
        }
        
        // Use the order's getBIRDiscount method
        const discountInfo = order.getBIRDiscount();
        if (!discountInfo) {
            return null;
        }
        
        return {
            name: discountInfo.type?.name || "BIR Discount",
            percent: discountInfo.type?.discount_percent || 20,
            amount: order.getBirDiscountAmount ? order.getBirDiscountAmount() : 0,
            grossSales: order.getBirDiscountableGrossSales ? order.getBirDiscountableGrossSales() : 0,
            isVatExempt: discountInfo.type?.is_vat_exempt ?? true,
            idNumber: order.getBirDiscountIdNumber ? order.getBirDiscountIdNumber() : '',
            idType: order.getBirDiscountIdType ? order.getBirDiscountIdType() : '',
        };
    },
    
    /**
     * Calculate VAT-exempt sales for display
     * Formula: Gross Sales ÷ 1.12
     */
    get vatExemptSales() {
        const info = this.birDiscountInfo;
        if (!info || !info.isVatExempt) {
            return 0;
        }
        return info.grossSales / 1.12;
    },
    
    /**
     * Calculate the discount amount on VAT-exempt sales
     * Formula: VAT-Exempt Sales × Discount%
     */
    get calculatedDiscount() {
        const info = this.birDiscountInfo;
        if (!info) {
            return 0;
        }
        if (info.isVatExempt) {
            return this.vatExemptSales * (info.percent / 100);
        }
        return info.grossSales * (info.percent / 100);
    },
});
