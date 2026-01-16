/** @odoo-module **/
/**
 * VoidOrderPopup - BIR-Compliant Void Transaction Popup
 * 
 * Simple void popup for POS interface with Manager PIN verification.
 * Voiding creates a record for BIR audit trail and marks the order as voided.
 */

import { Component, useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";

export class VoidOrderPopup extends Component {
    static template = "cai_pos.VoidOrderPopup";
    static components = { Dialog };
    static props = {
        order: Object,
        close: Function,
    };

    setup() {
        this.pos = usePos();
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        // Check if manager PIN is required
        const birConfig = this.getBirConfig();
        const requireAuth = birConfig?.require_manager_auth_for_void ?? false;
        const hasPin = !!birConfig?.id; // If there's a BIR config, we can verify PIN
        
        this.state = useState({
            // PIN verification state
            step: requireAuth && hasPin ? 'pin' : 'form', // 'pin' or 'form'
            managerPin: "",
            pinError: "",
            pinVerified: !requireAuth, // Skip verification if not required
            
            // Void form state
            voidReason: "",
            voidReasonDetails: "",
            isProcessing: false,
            errorMessage: "",
        });
        
        // Store if PIN is required for display purposes
        this.requireManagerAuth = requireAuth;
        
        // Predefined void reasons per BIR requirements
        this.voidReasons = [
            { value: "customer_request", label: _t("Customer Request"), description: _t("Customer requested to cancel this transaction.") },
            { value: "wrong_item", label: _t("Wrong Item Entered"), description: _t("Wrong item was entered in the order.") },
            { value: "wrong_price", label: _t("Wrong Price"), description: _t("Incorrect price was entered.") },
            { value: "wrong_quantity", label: _t("Wrong Quantity"), description: _t("Wrong quantity was entered.") },
            { value: "payment_error", label: _t("Payment Error"), description: _t("Payment processing error occurred.") },
            { value: "system_error", label: _t("System Error"), description: _t("System error during transaction processing.") },
            { value: "duplicate_transaction", label: _t("Duplicate Transaction"), description: _t("This is a duplicate of another transaction.") },
            { value: "order_cancelled", label: _t("Order Cancelled"), description: _t("Order was cancelled.") },
            { value: "other", label: _t("Other Reason"), description: "" },
        ];
    }
    
    /**
     * Get the BIR config from the POS data
     */
    getBirConfig() {
        try {
            // Access BIR config from POS data
            const birConfigs = this.pos.data?.['bir.config'];
            if (birConfigs && birConfigs.length > 0) {
                return birConfigs[0];
            }
            // Fallback: try to get from models
            const models = this.pos.models?.['bir.config'];
            if (models) {
                const configs = models.getAll();
                if (configs && configs.length > 0) {
                    return configs[0];
                }
            }
        } catch (e) {
            console.warn("[VOID] Could not get BIR config:", e);
        }
        return null;
    }

    get order() {
        return this.props.order;
    }
    
    get dialogTitle() {
        if (this.state.step === 'pin') {
            return _t("Manager Authorization Required");
        }
        return _t("Void Transaction");
    }
    
    // ========== PIN Verification Methods ==========
    
    onPinInput(ev) {
        // Only allow numeric input
        const value = ev.target.value.replace(/\D/g, '');
        this.state.managerPin = value.slice(0, 6); // Max 6 digits
        this.state.pinError = "";
    }
    
    async verifyPin() {
        if (!this.state.managerPin || this.state.managerPin.length < 4) {
            this.state.pinError = _t("Please enter a valid PIN (4-6 digits).");
            return;
        }
        
        this.state.isProcessing = true;
        this.state.pinError = "";
        
        try {
            const birConfig = this.getBirConfig();
            if (!birConfig) {
                // No BIR config - allow access
                this.state.pinVerified = true;
                this.state.step = 'form';
                return;
            }
            
            // Call backend to verify PIN
            const result = await this.orm.call(
                "bir.config",
                "verify_manager_pin",
                [birConfig.id, this.state.managerPin]
            );
            
            if (result.success) {
                this.state.pinVerified = true;
                this.state.step = 'form';
                this.notification.add(_t("Manager authorization verified."), { type: "success" });
            } else {
                this.state.pinError = result.message || _t("Invalid PIN. Please try again.");
                this.state.managerPin = "";
            }
        } catch (error) {
            console.error("[VOID] PIN verification error:", error);
            this.state.pinError = _t("Error verifying PIN. Please try again.");
        } finally {
            this.state.isProcessing = false;
        }
    }
    
    // ========== Void Form Methods ==========
    
    onReasonChange(ev) {
        this.state.voidReason = ev.target.value;
        // Auto-fill description based on selected reason
        const selectedReason = this.voidReasons.find(r => r.value === this.state.voidReason);
        if (selectedReason && selectedReason.description && !this.state.voidReasonDetails) {
            this.state.voidReasonDetails = selectedReason.description;
        }
    }
    
    onDetailsChange(ev) {
        this.state.voidReasonDetails = ev.target.value;
    }
    
    async confirmVoid() {
        // Validate inputs
        if (!this.state.voidReason) {
            this.state.errorMessage = _t("Please select a void reason.");
            return;
        }
        
        if (!this.state.voidReasonDetails || this.state.voidReasonDetails.trim().length < 5) {
            this.state.errorMessage = _t("Please provide a reason (minimum 5 characters).");
            return;
        }
        
        this.state.isProcessing = true;
        this.state.errorMessage = "";
        
        try {
            // Get order ID - handle both number and object with id property
            const orderId = typeof this.order.id === 'number' ? this.order.id : this.order.id;
            
            // Call backend to create void record
            const result = await this.orm.call(
                "pos.order",
                "create_void_from_pos",
                [[orderId], {
                    void_reason: this.state.voidReason,
                    void_reason_details: this.state.voidReasonDetails,
                    session_id: this.pos.session.id,
                }]
            );
            
            if (result.success) {
                this.notification.add(
                    _t("Order voided successfully: %s", result.void_number),
                    { type: "success" }
                );
                
                // Mark order as voided in frontend
                if (this.order) {
                    this.order.is_voided = true;
                }
                
                // Close the popup
                this.props.close();
            } else {
                this.state.errorMessage = result.error || _t("Failed to void order.");
            }
        } catch (error) {
            console.error("[VOID] Error:", error);
            this.state.errorMessage = error.message || _t("An error occurred.");
        } finally {
            this.state.isProcessing = false;
        }
    }
    
    cancel() {
        this.props.close();
    }
}
