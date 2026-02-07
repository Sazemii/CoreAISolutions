/** @odoo-module **/
/**
 * ManagerPinPopup - Simple Manager PIN Verification Popup
 * 
 * Used for operations that require manager authorization:
 * - Returns/Refunds
 * - Other sensitive operations as needed
 */

import { Component, useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";

export class ManagerPinPopup extends Component {
    static template = "cai_pos.ManagerPinPopup";
    static components = { Dialog };
    static props = {
        close: Function,
        onVerified: { type: Function, optional: true },
        onCancel: { type: Function, optional: true },
        title: { type: String, optional: true },
        message: { type: String, optional: true },
    };

    setup() {
        this.pos = usePos();
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        this.state = useState({
            managerPin: "",
            pinError: "",
            isProcessing: false,
        });
    }
    
    /**
     * Get the BIR config from the POS data
     */
    getBirConfig() {
        try {
            const birConfigs = this.pos.data?.['bir.config'];
            if (birConfigs && birConfigs.length > 0) {
                return birConfigs[0];
            }
            const models = this.pos.models?.['bir.config'];
            if (models) {
                const configs = models.getAll();
                if (configs && configs.length > 0) {
                    return configs[0];
                }
            }
        } catch (e) {
            console.warn("[PIN] Could not get BIR config:", e);
        }
        return null;
    }
    
    get title() {
        return this.props.title || _t("Manager Authorization");
    }
    
    get message() {
        return this.props.message || _t("Enter the Manager PIN to proceed.");
    }
    
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
                this.notification.add(_t("Manager authorization verified."), { type: "success" });
                this.props.onVerified?.();
                this.props.close();
                return;
            }
            
            // Call backend to verify PIN
            const result = await this.orm.call(
                "bir.config",
                "verify_manager_pin",
                [birConfig.id, this.state.managerPin]
            );
            
            if (result.success) {
                this.notification.add(_t("Manager authorization verified."), { type: "success" });
                this.props.onVerified?.();
                this.props.close();
            } else {
                this.state.pinError = result.message || _t("Invalid PIN. Please try again.");
                this.state.managerPin = "";
            }
        } catch (error) {
            console.error("[PIN] Verification error:", error);
            this.state.pinError = _t("Error verifying PIN. Please try again.");
        } finally {
            this.state.isProcessing = false;
        }
    }
    
    cancel() {
        this.props.onCancel?.();
        this.props.close();
    }
}


