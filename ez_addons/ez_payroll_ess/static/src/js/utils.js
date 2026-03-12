// JSON RPC

console.log('utils.js loaded');

async function jsonRpcApi(url, method, params) {
    const requestData = {
        jsonrpc: '2.0',
        method: method,
        params: params,
        id: 1
    };

    const body = JSON.stringify(requestData);
    console.log(`jsonRpcApi: url=${url} body=`, params);

    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body
    });
    const data = await response.json();
    console.log('jsonRpcApi Success: res=', data);
    return data;
}

async function updateModal(url, modal = 'modal_body', autoCreate = true) {
    const values = await jsonRpcApi(url, 'call', {});
    const res = values.result;
    const readonly = res.readonly ?? false;
    const modal_selector = `#${modal}`;

    $(modal_selector).children().remove().end();
    res.fields.forEach((fld, index) => {
        const selector = `#id_${fld.name}`;
        const label = `#label_${fld.name}`;

        if (autoCreate) {
            $(modal_selector).append(`<div id="div_${fld.name}" class="form-floating mb-1"></div>`);

            console.log(`updateModal: fld=`, fld.name);
            if ("selections" in fld) {
                $(`#div_${fld.name}`).append(`<select class="form-control" id="${selector.substring(1)}"></select>`)
                    .append(`<label class="control-label" id="${label.substring(1)}"></label>`);
                $(selector).children().remove().end();
                fld.selections.forEach((value, index) => {
                    console.log(` sel:`, value);
                    if (value[0] == fld.value) {
                        $(selector).append(`<option selected value="${value[0]}">${value[1]}</option>`);
                    } else {
                        $(selector).append(`<option value="${value[0]}">${value[1]}</option>`);
                    }
                });
            } else {
                const fld_type = fld.type ?? 'text';
                console.log(` val:`, fld.value);
                $(`#div_${fld.name}`).append(`<input class="form-control" id="${selector.substring(1)}" type="${fld_type}" value=""/>`)
                    .append(`<label class="control-label" id="${label.substring(1)}"></label>`);

                $(selector).val(fld.value || '');
            }
            $(label).html(fld.label || '');
        } else {
            // no autocreate fields view, only update values
            if ("selections" in fld) {
                $(selector).children().remove().end();
                fld.selections.forEach((value, index) => {
                    if (value[0] == fld.value) {
                        $(selector).append(`<option selected value="${value[0]}">${value[1]}</option>`);
                    } else {
                        $(selector).append(`<option value="${value[0]}">${value[1]}</option>`);
                    }
                });
            } else {
                $(selector).val(fld.value || '');
            }
        }

        if (readonly || (fld.readonly ?? false)) {
            $(selector).css('pointer-events', 'none');
            $(label).removeClass("fw-bold").removeClass('text-info');
        } else {
            $(selector).css('pointer-events', '');
            $(label).addClass("fw-bold").addClass('text-info');
        }
        console.log(`updateModal: ${selector}=`, fld.value);
    });

    console.log('updateModal: res=', res);
    return res;
}


function setFieldforWrite(form_fields) {
    const field_list = form_fields.filter(fld => !fld.readonly);
    return Object.assign({}, ...field_list.map((x) => ({
        [x.name]: $(`#id_${x.name}`).val()
    })));
}


async function unlinkRecords(api_url, checkboxesName) {
    const checkboxes = document.getElementsByName(checkboxesName);
    const values = Array.from(checkboxes)
        .filter(checkbox => checkbox.checked)
        .map(checkbox => parseInt(checkbox.value));
    if (values.length > 0 && confirm('Are you sure to DELETE these records?')) {
        await jsonRpcApi(api_url, 'call', { 'records': values });
        window.location.reload();
    }
}