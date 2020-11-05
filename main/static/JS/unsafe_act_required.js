function unsafe_act_change () {
    let reason_field = document.getElementById('id_reason');
    let unsafe_act_container = document.getElementById('div_id_unsafe_act');
    let unsafe_act_field = document.getElementById('id_unsafe_act');
    let details_field = document.getElementById('id_details');
    let details_span = document.getElementById('span_id_details');

    if (reason_field.options[reason_field.selectedIndex].value === '0') {
        unsafe_act_container.style.display = 'block';
        unsafe_act_field.required = true;
        details_field.required = true;
        details_span.style.display = 'inline';
    } else {
        unsafe_act_field.value = ''
        unsafe_act_field.required = false;
        details_field.required = false;
        details_span.style.display = 'none';
        unsafe_act_container.style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', function() {
   unsafe_act_change();
}, false);