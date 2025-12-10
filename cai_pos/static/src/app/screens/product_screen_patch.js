/** @odoo-module **/

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

/**
 * Patch PosStore to auto-apply BIR discount when new products are added
 * 
 * This is done at the store level (addLineToCurrentOrder) rather than ProductScreen
 * to ensure the discount is applied consistently.
 */
patch(PosStore.prototype, {
    async addLineToCurrentOrder(vals, opts = {}, configure = true) {
        const order = this.get_order();
        
        // Check if BIR discount is active BEFORE adding the line
        const hasBIRDiscount = order && order.bir_discount_type_id;
        
        // Call the original method to add the line
        const line = await super.addLineToCurrentOrder(...arguments);
        
        // After adding/merging the line, apply discount if active
        if (hasBIRDiscount && line && order) {
            // Apply discount to the newly added/merged line
            const discountApplied = order.applyBIRDiscountToLine(line);
            
            if (discountApplied) {
                // Trigger recompute to update totals
                order.recomputeOrderData();
            }
        }
        
        return line;
    },
});
