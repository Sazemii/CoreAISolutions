// UTILS

function on_change_date() {
    // var date_from = document.getElementById("date_from");
    // var date_to = document.getElementById("date_to");

    // if (date_from.value > date_to.value) {
    // }
}

function check_visibility() {
    console.log("Check Visibility");

    var request_unit_half = document.getElementById("request_unit_half");
    var request_unit_hours = document.getElementById("request_unit_hours");

    var id_request_hour = document.getElementById("id_request_hour");
    var id_date_to = document.getElementById("id_date_to");
    var id_date_am_pm = document.getElementById("id_date_am_pm");

    if ((!request_unit_half.checked) && (!request_unit_hours.checked)) {
        id_date_to.classList.remove('d-none');
        id_date_am_pm.classList.add('d-none');
        id_request_hour.classList.add('d-none');
    } else if ((!request_unit_half.checked) && (request_unit_hours.checked)) {
        id_date_to.classList.add('d-none');
        id_date_am_pm.classList.add('d-none');
        id_request_hour.classList.remove('d-none');
    } else if ((request_unit_half.checked) && (!request_unit_hours.checked)) {
        id_date_to.classList.add('d-none');
        id_date_am_pm.classList.remove('d-none');
        id_request_hour.classList.add('d-none');
    }
}

function click_change_unit_half() {
    var request_unit_half = document.getElementById("request_unit_half");
    var request_unit_hours = document.getElementById("request_unit_hours");

    if (request_unit_half.checked && request_unit_hours.checked) {
        request_unit_hours.checked = false;
    }
    check_visibility();
}

function click_change_unit_hours() {
    var request_unit_half = document.getElementById("request_unit_half");
    var request_unit_hours = document.getElementById("request_unit_hours");

    if (request_unit_half.checked && request_unit_hours.checked) {
        request_unit_half.checked = false;
    }
    check_visibility();
}

function submit_form_timeoff(event) {
    const submitter = event.submitter;
    // alert(submitter.value);
    if (submitter.value == 'Delete') {
        return confirm('Are you sure to DELETE this record?');
    } else {
        return true;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    check_visibility();
    console.log("Ready Portal!");
});

// ================================================
