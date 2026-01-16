/** @odoo-module **/

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { PosOrder } from "@point_of_sale/app/models/pos_order";

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

    // Initialize BIR discount properties directly on the order object
    this.bir_discount_type_id = vals.bir_discount_type_id || null;
    this.bir_discount_amount = vals.bir_discount_amount || 0;
    this.bir_discount_id_number = vals.bir_discount_id_number || "";
    this.bir_discount_id_type = vals.bir_discount_id_type || "";
    this.bir_discountable_gross_sales = vals.bir_discountable_gross_sales || 0;
  },

  /**
   * Apply BIR discount to a single NEW line (used when adding products to an order with active discount)
   *
   * BIR Regulation for SC/PWD Discounts (RA 9994, RA 10754):
   * 1. The original VAT-inclusive price is the starting point
   * 2. Remove VAT first (÷ 1.12) to get VAT-exempt base
   * 3. Apply 20% discount on the VAT-exempt base
   * 4. Final price = VAT-exempt base × 0.80
   *
   * Example: Item at ₱140 VAT-inclusive
   * - Step 1: VAT-exempt base = 140 ÷ 1.12 = ₱125
   * - Step 2: PWD discount = 125 × 20% = ₱25
   * - Step 3: Final price = 125 - 25 = ₱100
   * - Effective discount from ₱140 = (140-100)/140 = 28.57%
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

    // Store the original VAT-inclusive price BEFORE any changes
    // This is needed for correct BIR receipt calculations
    const originalPrices = line.get_all_prices(1);
    const originalVATInclusiveUnitPrice =
      originalPrices.priceWithTaxBeforeDiscount;

    // Store original price on the line for later reference
    if (!line.bir_original_vat_inclusive_price) {
      line.bir_original_vat_inclusive_price = originalVATInclusiveUnitPrice;
    }

    // Apply discount based on type (VAT-exempt or regular)
    if (discountType.is_vat_exempt) {
      const priceWithVAT = originalVATInclusiveUnitPrice;

      // Get the VAT rate from the product's original tax
      // Default to 12% for Philippine standard VAT
      let vatRate = 12.0;
      const productTaxes = product.taxes_id || [];
      for (const tax of productTaxes) {
        if (tax.amount_type === "percent" && tax.type_tax_use === "sale") {
          vatRate = tax.amount;
          break;
        }
      }
      const vatMultiplier = 1 + vatRate / 100;

      // BIR Formula: Remove VAT first, then apply discount
      // Step 1: Get VAT-exclusive price
      const priceWithoutVAT = priceWithVAT / vatMultiplier;
      // Step 2: Apply discount percentage on VAT-exclusive amount
      const finalPrice =
        priceWithoutVAT * (1 - discountType.discount_percent / 100);
      // Step 3: Calculate effective discount % relative to original VAT-inclusive price
      const effectiveDiscountPercent =
        ((priceWithVAT - finalPrice) / priceWithVAT) * 100;

      // Apply VAT-exempt tax if available
      // discountType.bir_tax_id could be an ID or a record, handle both cases
      let vatExemptTax = null;

      if (discountType.bir_tax_id) {
        vatExemptTax = discountType.bir_tax_id;

        // If bir_tax_id is a number (ID), look up the actual tax record
        if (
          typeof vatExemptTax === "number" ||
          typeof vatExemptTax === "string"
        ) {
          const taxModel = this.models["account.tax"];
          if (taxModel) {
            vatExemptTax = taxModel.get(parseInt(vatExemptTax));
          }
        }
      } else {
        // Fallback: Find any VAT-exempt (0%) tax in the system
        const taxModel = this.models["account.tax"];
        if (taxModel) {
          const allTaxes = taxModel.getAll ? taxModel.getAll() : [];
          vatExemptTax = allTaxes.find(
            (t) =>
              t.amount === 0 && t.type_tax_use === "sale" && t.active !== false
          );
        }
      }

      // Use update() with proper many2many command syntax to set tax_ids
      // This is required for Odoo 18's reactive model system
      // Command format: [["set", record1, record2, ...]] where records are tax objects
      if (vatExemptTax) {
        line.update({ tax_ids: [["set", vatExemptTax]] });
      }

      // Set discount percentage
      line.update({ discount: effectiveDiscountPercent });
    } else {
      line.update({ discount: discountType.discount_percent });
    }

    return true;
  },

  /**
   * Recalculate total BIR discount amount and gross sales from all lines
   *
   * This computes:
   * - discountable_gross_sales: Total VAT-inclusive amount of discountable items BEFORE discount
   * - bir_discount_amount: Total discount amount in currency
   */
  recalculateBIRDiscount() {
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
    let totalNonDiscountableGross = 0;
    let totalNonDiscountableVAT = 0;

    const orderlines = this.get_orderlines();
    for (const line of orderlines) {
      const product = line.get_product();

      // Get VAT rate from original product taxes
      let vatRate = 12.0; // Default Philippine VAT
      const productTaxes = product.taxes_id || [];
      for (const tax of productTaxes) {
        if (tax.amount_type === "percent" && tax.type_tax_use === "sale") {
          vatRate = tax.amount;
          break;
        }
      }
      const vatMultiplier = 1 + vatRate / 100;

      // Calculate VAT-inclusive price
      let vatInclusivePrice;
      if (line.bir_original_vat_inclusive_price) {
        vatInclusivePrice = line.bir_original_vat_inclusive_price * line.qty;
      } else {
        vatInclusivePrice = line.price_unit * vatMultiplier * line.qty;
      }

      // For non-discountable items, track their VAT but don't apply discount
      if (product.is_bir_discountable === false) {
        totalNonDiscountableGross += vatInclusivePrice;
        totalNonDiscountableVAT +=
          vatInclusivePrice - vatInclusivePrice / vatMultiplier;
        continue;
      }

      if (discountType.is_vat_exempt) {
        // For VAT-exempt discounts (PWD/SC):
        // The line's tax has been changed to VAT-exempt (0%), so we use
        // the VAT-inclusive price we calculated above
        totalGrossSales += vatInclusivePrice;

        // The discount amount is discount% of the VAT-exclusive amount
        const vatExclusiveAmount = vatInclusivePrice / vatMultiplier;
        const lineDiscountAmount =
          vatExclusiveAmount * (discountType.discount_percent / 100);
        totalDiscountAmount += lineDiscountAmount;
      } else {
        // For regular discounts: use the standard price calculations
        const prices = line.get_all_prices();
        const lineDiscountAmount =
          prices.priceWithTaxBeforeDiscount - prices.priceWithTax;
        totalDiscountAmount += lineDiscountAmount;
        totalGrossSales += prices.priceWithTaxBeforeDiscount;
      }
    }

    // Use update() to ensure reactivity and proper data persistence
    this.update({
      bir_discount_amount: totalDiscountAmount,
      bir_discountable_gross_sales: totalGrossSales,
      bir_non_discountable_gross: totalNonDiscountableGross,
      bir_non_discountable_vat: totalNonDiscountableVAT,
    });
  },

  /**
   * Override removeOrderline to recalculate BIR discount when lines are removed
   */
  removeOrderline(line) {
    const result = super.removeOrderline(...arguments);

    // Recalculate BIR discount after line removal
    if (this.bir_discount_type_id) {
      this.recalculateBIRDiscount();
    }

    return result;
  },

  /**
   * Override recomputeOrderData to also recalculate BIR discount
   */
  recomputeOrderData() {
    super.recomputeOrderData(...arguments);

    // Recalculate BIR discount when order data changes
    if (this.bir_discount_type_id) {
      this.recalculateBIRDiscount();
    }
  },

  export_as_JSON() {
    const json = super.export_as_JSON(...arguments);

    // Export BIR discount fields to JSON for backend persistence
    json.bir_discount_type_id = this.bir_discount_type_id || false;
    json.bir_discount_amount = this.bir_discount_amount || 0;
    json.bir_discount_id_number = this.bir_discount_id_number || "";
    json.bir_discount_id_type = this.bir_discount_id_type || "";
    json.bir_discountable_gross_sales = this.bir_discountable_gross_sales || 0;
    json.bir_non_discountable_gross = this.bir_non_discountable_gross || 0;
    json.bir_non_discountable_vat = this.bir_non_discountable_vat || 0;

    return json;
  },

  init_from_JSON(json) {
    super.init_from_JSON(...arguments);

    // Initialize BIR discount fields from JSON
    this.bir_discount_type_id = json.bir_discount_type_id || null;
    this.bir_discount_amount = json.bir_discount_amount || 0;
    this.bir_discount_id_number = json.bir_discount_id_number || "";
    this.bir_discount_id_type = json.bir_discount_id_type || "";
    this.bir_discountable_gross_sales = json.bir_discountable_gross_sales || 0;
    this.bir_non_discountable_gross = json.bir_non_discountable_gross || 0;
    this.bir_non_discountable_vat = json.bir_non_discountable_vat || 0;
  },

  export_for_printing(baseUrl, headerData) {
    const result = super.export_for_printing(baseUrl, headerData);
    result.is_reprint = Boolean(this.id);

    // Add BIR discount information for printing
    result.bir_discount = null;

    if (this.bir_discount_type_id) {
      // Recalculate to ensure fresh values before printing
      this.recalculateBIRDiscount();

      const birDiscountModel = this.models
        ? this.models["bir.discount.type"]
        : null;

      if (birDiscountModel) {
        const discountType = birDiscountModel.get(this.bir_discount_type_id);
        if (discountType) {
          // Calculate gross sales directly here for printing to ensure accuracy
          let printGrossSales = 0;
          let printDiscountAmount = 0;

          // Get VAT rate (default 12%)
          let vatRate = 12.0;

          const orderlines = this.get_orderlines();
          for (const line of orderlines) {
            const product = line.get_product();

            // Skip non-discountable items
            if (product.is_bir_discountable === false) {
              continue;
            }

            // Get VAT rate from product's original taxes
            const productTaxes = product.taxes_id || [];
            for (const tax of productTaxes) {
              if (
                tax.amount_type === "percent" &&
                tax.type_tax_use === "sale"
              ) {
                vatRate = tax.amount;
                break;
              }
            }
            const vatMultiplier = 1 + vatRate / 100;

            // CRITICAL: Use saved bir_original_vat_inclusive_price if available
            // This was captured BEFORE the tax was changed to VAT-exempt
            let originalVATInclusivePrice;
            if (line.bir_original_vat_inclusive_price) {
              // Saved price was per unit, multiply by qty
              originalVATInclusivePrice =
                line.bir_original_vat_inclusive_price * line.qty;
            } else {
              // Fallback: calculate from price_unit assuming it's base price
              originalVATInclusivePrice =
                line.price_unit * vatMultiplier * line.qty;
            }
            printGrossSales += originalVATInclusivePrice;

            if (discountType.is_vat_exempt) {
              // Discount is on VAT-exempt base (price without VAT)
              const vatExemptBase = originalVATInclusivePrice / vatMultiplier;
              printDiscountAmount +=
                vatExemptBase * (discountType.discount_percent / 100);
            }
          }

          result.bir_discount = {
            name: discountType.name,
            code: discountType.code,
            percent: discountType.discount_percent,
            amount: printDiscountAmount || this.bir_discount_amount || 0,
            id_number: this.bir_discount_id_number || "",
            id_type: this.bir_discount_id_type || "",
            is_vat_exempt: discountType.is_vat_exempt,
            discountable_gross_sales:
              printGrossSales || this.bir_discountable_gross_sales || 0,
            non_discountable_gross: this.bir_non_discountable_gross || 0,
            non_discountable_vat: this.bir_non_discountable_vat || 0,
          };
        }
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

  /**
   * Calculate BIR-compliant VAT breakdown for receipt printing
   *
   * This computes:
   * - vatable_sales: Base amount subject to VAT (net of VAT)
   * - vat_amount: 12% VAT on vatable sales
   * - vat_exempt_sales: Sales exempt from VAT (SC/PWD discounted)
   * - zero_rated_sales: Sales at 0% VAT rate (exports, etc.)
   *
   * For VAT-inclusive pricing with price_include=True taxes:
   * - The order total IS the VAT-inclusive amount
   * - vatable_sales = order_total / 1.12
   * - vat_amount = order_total - vatable_sales
   */
  _calculateBIRVATBreakdown(printData) {
    const breakdown = {
      vatable_sales: 0,
      vat_amount: 0,
      vat_exempt_sales: 0,
      zero_rated_sales: 0,
    };

    const hasVATExemptDiscount =
      printData.bir_discount && printData.bir_discount.is_vat_exempt;

    if (hasVATExemptDiscount) {
      // For VAT-exempt orders (SC/PWD discount applied):
      // - Discounted items become VAT-exempt
      // - Non-discountable items KEEP their VAT

      // Get non-discountable amounts from bir_discount data
      const nonDiscountableGross =
        printData.bir_discount.non_discountable_gross || 0;
      const nonDiscountableVAT =
        printData.bir_discount.non_discountable_vat || 0;
      const nonDiscountableBase = nonDiscountableGross - nonDiscountableVAT;

      // Non-discountable items are vatable
      breakdown.vatable_sales = nonDiscountableBase;
      breakdown.vat_amount = nonDiscountableVAT;

      // VAT-exempt is the total order minus the non-discountable gross
      // (because non-discountable items are already VAT-inclusive in the total)
      const orderTotal = printData.taxTotals?.order_total || 0;
      breakdown.vat_exempt_sales = orderTotal - nonDiscountableGross;

      return breakdown;
    }

    // For regular orders, try to get VAT info from tax subtotals
    if (printData.taxTotals && printData.taxTotals.subtotals) {
      for (const subtotal of printData.taxTotals.subtotals) {
        const taxAmount = subtotal.tax_amount_currency || 0;
        const baseAmount = subtotal.base_amount_currency || 0;

        if (taxAmount > 0) {
          breakdown.vatable_sales += baseAmount;
          breakdown.vat_amount += taxAmount;
        } else if (baseAmount > 0) {
          // Zero-rated or exempt items without BIR discount
          breakdown.zero_rated_sales += baseAmount;
        }
      }
    }

    // Fallback: If we have an order total but no VAT breakdown was computed,
    // compute from the order total assuming 12% VAT-inclusive pricing
    if (
      breakdown.vatable_sales === 0 &&
      breakdown.vat_amount === 0 &&
      breakdown.zero_rated_sales === 0 &&
      printData.taxTotals
    ) {
      const orderTotal = printData.taxTotals.order_total || 0;
      if (orderTotal > 0) {
        // Assume 12% VAT-inclusive: total = base + (base * 0.12) = base * 1.12
        // Therefore: base = total / 1.12
        breakdown.vatable_sales = orderTotal / 1.12;
        breakdown.vat_amount = orderTotal - breakdown.vatable_sales;
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
        amount: this.bir_discount_amount || 0,
        id_number: this.bir_discount_id_number || "",
        id_type: this.bir_discount_id_type || "",
      };
    }

    const birDiscountModel = this.models["bir.discount.type"];
    const discountType = birDiscountModel.get(this.bir_discount_type_id);

    if (!discountType) {
      return {
        type: { name: "Unknown Discount", discount_percent: 0 },
        amount: this.bir_discount_amount || 0,
        id_number: this.bir_discount_id_number || "",
        id_type: this.bir_discount_id_type || "",
      };
    }

    return {
      type: discountType,
      amount: this.bir_discount_amount || 0,
      id_number: this.bir_discount_id_number || "",
      id_type: this.bir_discount_id_type || "",
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
      const orderlines = this.get_orderlines();

      for (const line of orderlines) {
        line.discount = 0;
        // Restore original taxes
        const product = line.get_product();
        if (product && product.taxes_id) {
          line.tax_ids = product.taxes_id;
        }
      }

      // Use update() to ensure data is properly cleared and persisted
      this.update({
        bir_discount_type_id: null,
        bir_discount_amount: 0,
        bir_discount_id_number: "",
        bir_discount_id_type: "",
        bir_discountable_gross_sales: 0,
      });

      // Recompute order totals
      this.recomputeOrderData();
    } catch (e) {
      console.warn("[BIR] Error removing discount:", e);
    }

    return true;
  },
});
