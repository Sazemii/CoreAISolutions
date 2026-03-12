/** @odoo-module **/
import { Component, useState, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class FormInputWidget extends Component {
    static template = xml`
        <div class="form-floating mb-1">
            <t t-if="props.type=='selection'">
                <t t-if="props.readonly" >
                    <t t-foreach="props.selection" t-as="sel" t-key="sel[0]">
                        <input class="form-control" t-if="sel[0]==props.value" 
                            type="text" t-att-value="sel[1]" readonly="1"/>
                    </t>
                </t>
                <select t-else=""
                    class="form-control" 
                    t-model="props.prev_state.record[props.name]" 
                    t-on-change="_onFieldInputChanged"
                >
                    <t t-foreach="props.selection" t-as="sel" t-key="sel[0]">
                        <option t-att-value="sel[0]">
                            <t t-esc="sel[1]"/>
                        </option>
                    </t>
                </select>
            </t><t t-else="">
                <input t-if="props.readonly"
                    class="form-control" 
                    t-att-readonly="props.readonly"
                    t-att-type="inputType"
                    t-att-value="props.value"
                />
                <input t-else=""
                    class="form-control" 
                    t-model="props.prev_state.record[props.name]" 
                    t-att-type="inputType"
                    t-att-value="props.value"
                    t-on-input="_onFieldInputChanged"
                />
            </t>
            <label class="control-label">
                <t t-esc="props.label"/>
            </label>
        </div>
    `;

    setup() {
        this.inputType = this.props.type || "text";
    }

    _onFieldInputChanged(ev) {
        this.props.prev_state.isEdited = true;
        console.log("Form has been modified!");
    }
}