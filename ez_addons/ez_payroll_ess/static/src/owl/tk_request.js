/** @odoo-module **/
import { Component, useState, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { FormInputWidget } from "./form_input";

// ####################################################

export class TkStatePillWidget extends Component {
    static template = xml`
        <t t-set="rec" t-value="props.data"/>
        <div>
            <div t-if="rec.state=='denied'" t-esc="props.lookup[rec.state]" class="badge rounded-pill text-bg-danger"/>
            <div t-elif="rec.state=='sent'" t-esc="props.lookup[rec.state]" class="badge rounded-pill text-bg-warning"/>
            <div t-elif="rec.state=='approved'" t-esc="props.lookup[rec.state]" class="badge rounded-pill text-bg-success"/>
            <div t-else="" t-esc="props.lookup[rec.state]" class="badge rounded-pill text-bg-secondary"/>
        </div>
    `;
}

export class TkRequestDialog extends Component {
    static template = "ez_payroll_ess.TkRequestDialog";
    static components = { Dialog, FormInputWidget };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            id: this.props.record.id,
            record: this.props.record,
            lookups: this.props.lookups,
            selections: this.props.selections,
            isEdited: false,
        });
        this.colorBackgroundLookup = {
            'draft': 'bg-danger',
            'sent': 'bg-warning',
            'approved': 'bg-secondary',
            'denied': 'bg-danger',
        };
        console.log("TkRequestDialog opened with record:", this.props);
    }

    async _readData() {
        const recs = await this.orm.rpc(`/my/tkrequest/read/${this.state.record.id}/0`, {
            fields: ['id', 'employee_id', 'name', 'date', 'type', 'day_type', 'auth_hrs', 'schedule', 'time', 'note', 'state'],
        });
        if (recs && recs.length > 0) {
            const rec = recs[0]; // rpc returns a list of records, we need the first one   
            this.state.record.employee_id = rec.employee_id;
            this.state.record.name = rec.name;
            this.state.record.date = rec.date;
            this.state.record.type = rec.type;
            this.state.record.day_type = rec.day_type;
            this.state.record.auth_hrs = rec.auth_hrs;
            this.state.record.schedule = rec.schedule;
            this.state.record.time = rec.time;
            this.state.record.note = rec.note
            this.state.record.state = rec.state
            this.state.isEdited = false;
        }
    }

    async _onConfirm() {
        console.log("SAVE:", this.state)
        await this.orm.rpc(`/my/tkrequest/write/${this.state.record.id}/0`, {
            employee_id: this.state.record.employee_id[0],
            name: this.state.record.name,
            date: this.state.record.date,
            type: this.state.record.type,
            day_type: this.state.record.day_type,
            auth_hrs: parseFloat(this.state.record.auth_hrs, 10) || 0,
            schedule: this.state.record.schedule,
            time: this.state.record.time,
            note: this.state.record.note,
            state: this.state.record.state,
        });
        this.state.isEdited = false;

        this._readData();

        this.props.onSave({
            values: this.state.record,
        });
        // this.props.close(); // Standard prop passed by dialogService
    }

    async _deleteRecord() {
        if (confirm('Are you sure to delete this record?')) {
            await this.orm.rpc(`/my/tkrequest/unlink/${this.props.record.id}`);
            this.props.close()
            window.location.reload();
        }
    }

    async _forApproval() {
        if (confirm('Submit this request for approval?')) {
            await this.orm.rpc(`/my/tkrequest/write/${this.state.record.id}/0`, { state: 'sent' });
            this.state.record.state = 'sent';
            this.state.isEdited = false;
            // this.props.onSave({
            //     values: this.state.record,
            // });
            // this.props.close(); // Standard prop passed by dialogService
        }
    }

    _quitDialog() {
        if (this.state.isEdited) {
            if (confirm('You have unsaved changes. Do you want to discard them?')) {
                this._readData();
                this.props.close()
            }
        } else {
            this.props.close();
        }
        // window.location.reload();
    }

    _approveRequest() {
        if (confirm('Approve this request?')) {
            this.orm.rpc(`/my/tkrequest/state/approved/${this.state.record.id}/1`);
            this.state.record.state = 'approved';
            this.state.isEdited = false;
        }
    }

    _denyRequest() {
        if (confirm('Deny this request?')) {
            this.orm.rpc(`/my/tkrequest/state/denied/${this.state.record.id}/1`);
            this.state.record.state = 'denied';
            this.state.isEdited = false;
        }
    }

}

// ####################################################

export class TkRequestCardWidget extends Component {
    static template = "ez_payroll_ess.TkRequestCardWidget";
    static components = { TkStatePillWidget };
    setup() {
        this.orm = useService("orm");
        this.dialogService = useService("dialog");
        this.state = useState({
            // id: this.props.record.id,
            record: this.props.record,
            lookups: this.props.lookups,
            selections: this.props.selections,
        });
        console.log("TkRequestCardWidget:", this.props);
    }

    _onItemClick(record) {
        console.log(`Clicked ${record.name}`);
        this.dialogService.add(TkRequestDialog, {
            record: record,
            lookups: this.state.lookups,
            selections: this.state.selections,
            approve: this.props.approve,
            onSave: (data) => {
                console.log("Saved:", data.values);
                // this.state.record = data.values;
            }
        });
    }
}
// console.log("Registering TkRequestCardtWidget");

// ######################################################

export class TimekeepingPortaltWidget extends Component {
    // static template = "ez_payroll_ess.TimekeepingPortaltWidget";
    static props = ["*"];
    static components = { TkRequestCardWidget };
    static template = xml`
        <div class="row">

            <div class="col-md-4" t-if="props.approve == 0">
                <div class="card shadow bg-secondary rounded mb-3">
                    <div class="card-body" t-on-click="() => this._newRecord()">
                        <div>
                            Add new record...
                        </div>
                        <div class="d-flex justify-content-center align-items-center mt-2 mb-2" role="button">
                            <i class="fa fa-plus fa-6x" role="button"/>
                        </div>
                    </div>
                </div>
            </div>

            <t t-foreach="props.records" t-as="r" t-key="r.id">
                <TkRequestCardWidget 
                    record="r" 
                    lookups="props.lookups" 
                    approve="props.approve"
                    selections="props.selections"
                />
            </t>
        </div>
    `

    setup() {
        this.orm = useService("orm");
        // this.action = useService("action");
        console.log("Opening requests...", this.props.records);
    }

    async _newRecord() {
        console.log("Creating new record for employee_id:", this.props.employee_id);
        if (confirm('Create new timekeeping request?')) {
            const rec_id = await this.orm.rpc(`/my/tkrequest/write/0/0`, {
                employee_id: this.props.employee_id,
                name: "New Request",
            });
            window.location.reload();
        }
    }
}

// Register it so the frontend can find it by name
console.log("Registering ez_payroll_ess.TimekeepingPortaltWidget");
registry.category("public_components").add("ez_payroll_ess.TimekeepingPortaltWidget", TimekeepingPortaltWidget);

// ######################################################

