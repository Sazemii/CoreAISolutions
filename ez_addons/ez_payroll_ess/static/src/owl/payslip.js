/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
// import { useService } from "@web/core/utils/hooks";

export class PayslipWidget extends Component {
    static template = "ez_payroll_ess.PayslipWidget";
    static props = ["*"];

    setup() {
        // this.orm = useService("orm");
        // this.action = useService("action");
    }

    increment() {
        this.state.count++;
    }

    open_payslip() {
        console.log("Opening payslip...");
        // this.action.doAction({
        //     type: "ir.actions.act_window",
        //     res_model: "hr.payslip",
        //     res_id: this.props.payslip_id,
        //     views: [[false, "form"]],
        //     target: "new",
        // });
    }
}

// Register it so the frontend can find it by name
console.log("Registering ez_payroll_ess.PayslipWidget");
registry.category("public_components").add("ez_payroll_ess.PayslipWidget", PayslipWidget);
// console.log("Registering ez_payroll_ess.PayslipWidget 2");
