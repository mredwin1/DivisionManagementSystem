function reason_change () {
    let reason_field = document.getElementById('id_reason');
    let other_reason_container = document.getElementById('div_id_other_reason');
    let other_reason_field = document.getElementById('id_other_reason');

    if (reason_field.options[reason_field.selectedIndex].value === 'Other') {
        other_reason_container.style.display = 'block';
        other_reason_field.required = true;
    } else {
        console.log(other_reason_field)
        other_reason_field.value = ''
        other_reason_field.required = false;
        other_reason_container.style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    reason_change();
}, false);