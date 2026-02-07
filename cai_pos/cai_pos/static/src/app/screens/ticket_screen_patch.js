/** @odoo-module **/
/**
 * Ticket Screen Patch for BIR Void and Return Functionality
 *
 * Adds:
 * - VOID button to paid orders with Manager PIN verification
 * - Manager PIN verification for REFUND/RETURN operations
 */

import { patch } from "@web/core/utils/patch";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { VoidOrderPopup } from "@cai_pos/app/popups/void_popup/void_popup";
import { ManagerPinPopup } from "@cai_pos/app/popups/manager_pin_popup/manager_pin_popup";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

patch(TicketScreen.prototype, {
  setup() {
    super.setup(...arguments);
    this.dialog = useService("dialog");
    this.notification = useService("notification");
    this.orm = useService("orm");
  },

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
      console.warn("[BIR] Could not get BIR config:", e);
    }
    return null;
  },

  /**
   * Check if manager PIN is required for returns
   */
  requiresManagerAuthForReturn() {
    const birConfig = this.getBirConfig();
    return birConfig?.require_manager_auth_for_return ?? false;
  },

  /**
   * Verify manager PIN
   * Returns a promise that resolves to true if verified, false otherwise
   */
  async verifyManagerPin() {
    const birConfig = this.getBirConfig();
    if (!birConfig) {
      return true; // No config, allow access
    }

    return new Promise((resolve) => {
      this.dialog.add(ManagerPinPopup, {
        onVerified: () => resolve(true),
        onCancel: () => resolve(false),
      });
    });
  },

  /**
   * Override _onDoRefund to add manager PIN verification
   * This is called when the user clicks the Refund button
   */
  async _onDoRefund() {
    if (this.requiresManagerAuthForReturn()) {
      const verified = await this.verifyManagerPin();
      if (!verified) {
        this.notification.add(_t("Manager authorization required for returns."), {
          type: "warning",
        });
        return;
      }
    }
    // Call the original refund method
    return super._onDoRefund(...arguments);
  },

  /**
   * Check if order can be voided
   * Only check if order is paid and not already voided
   * IMPORTANT: Only allow voiding orders from the CURRENT session
   */
  canVoidOrder(order) {
    if (!order) return false;

    // Order must be in paid/done/invoiced state
    const isPaid =
      order.state === "paid" ||
      order.state === "done" ||
      order.state === "invoiced";
    if (!isPaid) {
      return false;
    }

    // Order must not already be voided
    if (order.is_voided) {
      return false;
    }

    // Session must be open (check current session, not order's session)
    const session = this.pos.session;
    if (!session) return false;

    const sessionOpen = [
      "opened",
      "opening_control",
      "closing_control",
    ].includes(session.state);
    if (!sessionOpen) {
      return false;
    }

    // CRITICAL: Order must belong to the CURRENT session
    // Orders from other sessions cannot be voided from this session
    // Get order's session ID - handle both object and scalar forms
    const orderSessionId = order.session_id?.id || order.session_id;
    const currentSessionId = session.id;

    if (orderSessionId !== currentSessionId) {
      return false;
    }

    return true;
  },

  /**
   * Show void popup for the selected order
   */
  async onVoidOrder(order) {
    if (!order) {
      this.notification.add(_t("No order selected"), { type: "warning" });
      return;
    }

    if (!this.canVoidOrder(order)) {
      let message = _t("Cannot void this order.");

      if (order.state === "draft") {
        message = _t(
          "Order is not paid yet. Use 'Cancel Order' (trash icon) instead."
        );
      } else if (order.state === "cancel") {
        message = _t("Order is already cancelled.");
      } else if (order.is_voided) {
        message = _t("Order is already voided.");
      } else if (
        !["opened", "opening_control", "closing_control"].includes(
          this.pos.session?.state
        )
      ) {
        message = _t("Session is closed. Please open a session first.");
      } else {
        // Check if order is from a different session
        const orderSessionId = order.session_id?.id || order.session_id;
        const currentSessionId = this.pos.session?.id;
        if (orderSessionId !== currentSessionId) {
          message = _t(
            "Cannot void orders from other sessions. Only orders from the current session can be voided."
          );
        }
      }

      this.notification.add(message, { type: "warning" });
      return;
    }

    // Open void popup (which handles its own PIN verification)
    this.dialog.add(VoidOrderPopup, {
      order: order,
    });
  },

  /**
   * Check if void button should be shown for this order
   */
  shouldShowVoidButton(order) {
    return this.canVoidOrder(order);
  },
});
