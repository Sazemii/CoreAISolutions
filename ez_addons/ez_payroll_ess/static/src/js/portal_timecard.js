// Timecard JS

function submit_form_timecard(event) {
    const submitter = event.submitter;
    if (submitter.value == 'Delete') {
        return confirm('Are you sure to DELETE this record?');
    } else {
        return true;
    }
}

async function timecards_unlink_api(values) {
    console.log('timecards_unlink_api:', values);
    if (values.length > 0 && confirm('Are you sure to DELETE these records?')) {
        await jsonRpcApi('/my/timecard/unlink', 'call', { 'records': values })
        window.location.reload();
    }
}

function unlink_timecards() {
    const checkboxes = document.getElementsByName('unlink');
    const values = Array.from(checkboxes)
        .filter(checkbox => checkbox.checked)
        .map(checkbox => parseInt(checkbox.value));
    timecards_unlink_api(values);
}

// MODAL #########################
var timecard_show_modal = async function (id) {
    const values = await jsonRpcApi(`/my/timerecord/get/${id}`, 'call', {});
    const res = values.result;

    const day_type_selections = {
        reg: 'Regular Day',
        do: 'Rest Day',
        lh: 'Regular Holiday',
        sh: 'Special H',
        do_lh: 'Reg. Hol. and Rest Day',
        do_sh: 'Spec. Hol. and Rest Day',
    };

    const readonly = $('#approve').val() == '1' || res.state != 'draft';
    console.log(`timecard_show_modal: readonly=${readonly}`);

    $('#modal_title').html(res.employee_id[1]);
    $('#trec_date').val(`${res.name} ${day_type_selections[res.day_type]}`);
    // $('#trec_day_type').val(day_type_selections[res.day_type]);
    $('#trec_schedule').val(res.schedule || '');

    $('#trec_timelog').val(res.timelog || '');
    $('#trec_timelog').attr('readonly', readonly);

    $('#trec_auth_hrs').val(res.auth_hrs);
    $('#trec_norm_ot').val(`${res.vnorm_time || ''} ${res.vot_time && '/' || ''} ${res.vot_time}`);
    $('#trec_remarks').val(res.vremarks || '');

    $('#trec_notes').val(res.note || '');
    $('#trec_notes').attr('readonly', readonly);

    if (readonly) {
        $('#trec_save').addClass('d-none');
        $('#trec_delete').addClass('d-none');
    } else {
        $('#trec_save').removeClass('d-none');
        $('#trec_delete').removeClass('d-none');
    }

    $('#timerec_id').val(id);
    $('#detailsModal').modal('show');
}

var timerecord_saved = false;
async function timerecord_save() {
    const id = $('#timerec_id').val();
    const resv = await jsonRpcApi(`/my/timerecord/write/${id}`, 'call', {
        'timelog': $('#trec_timelog').val(),
        'note': $('#trec_notes').val(),
    });
    console.log(`timecard_write: ${resv.result}`)
    timerecord_saved = true;
    timecard_show_modal(id);
}

async function timerecord_delete() {
    if (confirm('Are you sure to DELETE this record?')) {
        const id = $('#timerec_id').val();
        const resv = await jsonRpcApi(`/my/timerecord/unlink/${id}`, 'call');
        console.log(`timecard_delete: ${resv.result}`)
        location.reload();
    }
}

function set_close_event() {
    console.log('set_close_event Ready');

    const myModal = document.getElementById('detailsModal');
    myModal.addEventListener('hidden.bs.modal', event => {
        console.log('Modal closed!', timerecord_saved);
        if (timerecord_saved) location.reload();
    });
}

async function unlink_timerecords() {
    const api_url = '/my/timerecord/unlink';
    const checkboxes = document.getElementsByName('timerecord_unlink');
    const values = Array.from(checkboxes)
        .filter(checkbox => checkbox.checked)
        .map(checkbox => parseInt(checkbox.value));
    if (values.length > 0 && confirm('Are you sure to DELETE these records?')) {
        await jsonRpcApi(api_url, 'call', { 'records': values })
        window.location.reload();
    }
}


