
async function unlink_timeoffs() {
    const api_url = '/my/timeoff/unlink';
    const checkboxes = document.getElementsByName('unlink_timeoff');
    const values = Array.from(checkboxes)
        .filter(checkbox => checkbox.checked)
        .map(checkbox => parseInt(checkbox.value));
    if (values.length > 0 && confirm('Are you sure to DELETE these records?')) {
        await jsonRpcApi(api_url, 'call', { 'records': values })
        window.location.reload();
    }
}
