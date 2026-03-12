// UTILS

var form_fields = [];
var rec_id = 0;

async function record_show(id, approve) {
    rec_id = id;
    const res = await updateModal(`/my/tkrequest/get/${id}/${approve}`);
    if (approve) {
        $('#btn_save').hide();
        $('#btn_for_approval').hide();
        $('#btn_draft').hide();
        if (res.state == 'sent') {
            $('#btn_approve').show();
            $('#btn_deny').show();
        } else if (res.state == 'denied') {
            $('#btn_approve').hide();
            $('#btn_deny').hide();
        } else {
            $('#btn_approve').hide();
            $('#btn_deny').show();
        }
    } else {
        $('#btn_deny').hide();
        $('#btn_approve').hide();
        $('#btn_draft').hide();
        if (res.state == 'draft') {
            $('#btn_for_approval').show();
            $('#btn_save').show();
        } else {
            $('#btn_for_approval').hide();
            $('#btn_save').hide();
            if (res.state == 'denied')
                $('#btn_draft').show();
        }
    }
    form_fields = res.fields;

    $('#id_type').change(function () {
        change_type_field(form_fields);
    });

    change_type_field();
    $('#tkrequest_modal').modal('show');
}

function change_type_field() {
    // hide selectable fields
    $('#id_auth_hrs').hide();
    $('#id_time').hide();
    $('#id_day_type').hide();
    $('#id_schedule').hide();
    if ($('#id_type').val() == 'ot') {
        $('#id_auth_hrs').show();
    } else if ($('#id_type').val() == 'ob') {
        $('#id_auth_hrs').show();
        $('#id_time').show();
    } else if ($('#id_type').val() == 'sch') {
        $('#id_day_type').show();
        $('#id_schedule').show();
    }
}

var record_saved = false;
async function record_save(approve) {
    const val = setFieldforWrite(form_fields);
    const res = await jsonRpcApi(`/my/tkrequest/write/${rec_id}/${approve}`, 'call', val);
    rec_id = res.result;
    record_saved = true;
    record_show(rec_id, approve);
    console.log(`record_save: id, val =`, rec_id, val);
}

function set_close_event() {
    console.log('set_close_event Ready');
    const myModal = document.getElementById('tkrequest_modal');
    myModal.addEventListener('hidden.bs.modal', event => {
        console.log('Modal closed!', record_saved);
        if (record_saved) location.reload();
    });
}

function unlink_tkrequests() {
    unlinkRecords('/my/tkrequest/unlink', 'unlink_checbox_record');
}


async function record_state(approve, state) {
    if (rec_id) {
        const res = await jsonRpcApi(`/my/tkrequest/state/${state}/${rec_id}/${approve}`, 'call', {});
        record_saved = true;
        record_show(rec_id, approve);
        console.log(`record_for_approval: id=${rec_id} res=`, res.result);
    }
}
