/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

export class DashboardViewer extends Component {
    static template = "datumsAI.DashboardViewer";
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            dashboards: [],
            currentUrl: this.props.action.params.url || "",
            loading: true,
            error: null,
            showInstructions: true,
            isMaintenance: false,
            sidebarCollapsed: window.innerWidth <= 1500,
        });

        onWillStart(async () => {
            const [configs, config] = await Promise.all([
                this.orm.silent.searchRead('datums.config', [], ['datums_access_key', 'datums_secret_key']),
                this.orm.silent.call('datums.script', 'get_user_companies_config', [])
            ]);

            const accessKey = configs && configs.length > 0 ? configs[0].datums_access_key : "";
            const secretKey = configs && configs.length > 0 ? configs[0].datums_secret_key : "";

            if (accessKey && secretKey) {
                this.state.showInstructions = false;
            } else {
                this.state.showInstructions = true;
            }
            this.userCompaniesConfig = config;
            await this.loadDashboards();
        });
    }

    async loadDashboards() {
        try {
            const payload = {};
            if (this.userCompaniesConfig) {
                payload.filter = this.userCompaniesConfig;
            }

            const res = await fetch('/datums/get_dashboard_pages', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (res.status !== 200) {
                this.state.isMaintenance = true;
                this.state.loading = false;
                return;
            }

            const json = await res.json();

            if (!json.success) {
                console.warn("Dashboard API error:", json.error);
                if (json.maintenance) {
                    this.state.isMaintenance = true;
                    this.state.loading = false;
                    return;
                }
            }

            const isV16 = (session && session.server_version && session.server_version.startsWith('16')) || false;
            const iconDir = isV16 ? '/datums/static/src/img/icons16/' : '/datums/static/src/img/icons/';

            const nameToIconMap = {
                // General/Dashboards
                'default': iconDir + 'board.svg',
                'summary': iconDir + 'spreadsheet.svg',

                // Sales
                'sales': iconDir + 'sale.svg',
                'sale': iconDir + 'sale.svg',
                'crm': iconDir + 'crm.svg',
                'subscription': iconDir + 'sale_subscription.svg',
                'subscriptions': iconDir + 'sale_subscription.svg',
                'point of sales': iconDir + 'point_of_sale.svg',
                'point of sale': iconDir + 'point_of_sale.svg',
                'pos': iconDir + 'point_of_sale.svg',

                // Finance
                'accounting': iconDir + 'accountant.svg',
                'invoicing': iconDir + (isV16 ? 'account.png' : 'account.svg'),
                'expense': iconDir + 'hr_expense.svg',
                'expenses': iconDir + 'hr_expense.svg',

                // Inventory & Manufacturing
                'inventory': iconDir + 'stock.svg',
                'manufacturing': iconDir + 'mrp.svg',
                'purchase': iconDir + 'purchase.svg',
                'plm': iconDir + 'mrp_plm.svg',
                'maintenance': iconDir + 'maintenance.svg',
                'quality': iconDir + 'quality.svg',

                // Human Resources
                'employee': iconDir + 'hr.svg',
                'employees': iconDir + 'hr.svg',
                'time off': iconDir + 'hr_holidays.svg',
                'fleet': iconDir + 'fleet.svg',

                // Services
                'project': iconDir + 'project.svg',
                'helpdesk': iconDir + 'helpdesk.svg',
                'timesheet': iconDir + (isV16 ? 'hr_timesheet.png' : 'hr_timesheet.svg'),
                'timesheets': iconDir + (isV16 ? 'hr_timesheet.png' : 'hr_timesheet.svg'),
                'field service': iconDir + 'industry_fsm.svg',
            };

            const getIconForName = (name) => {
                if (!name) return null;
                const normalized = name.toLowerCase().trim();
                if (nameToIconMap[normalized]) {
                    return nameToIconMap[normalized];
                }
                for (const key of Object.keys(nameToIconMap)) {
                    if (normalized.includes(key)) {
                        return nameToIconMap[key];
                    }
                }
                return null;
            };

            // Map API shape → { id, name, dashboard_link } expected by the XML template
            this.state.dashboards = (json.pages || []).map(p => ({
                id: p.id,
                name: p.name,
                dashboard_link: p.url,
                icon: getIconForName(p.name),
            }));

            // If no URL was passed from action, use the first dashboard
            if (!this.state.currentUrl && this.state.dashboards.length > 0) {
                this.state.currentUrl = this.state.dashboards[0].dashboard_link;
            }

            this.state.loading = false;
        } catch (error) {
            console.error("Failed to load dashboards:", error);
            this.state.error = error.message;
            this.state.loading = false;
        }
    }

    selectDashboard(dashboard) {
        this.state.currentUrl = dashboard.dashboard_link;
    }

    goHome() {
        window.location.href = "/web";
    }

    closeInstructions() {
        this.state.showInstructions = false;
    }

    openSettings() {
        this.action.doAction("base_setup.action_general_configuration");
    }

    toggleSidebar() {
        this.state.sidebarCollapsed = !this.state.sidebarCollapsed;
    }
}

registry.category("actions").add("dashboard_viewer_action", DashboardViewer);
