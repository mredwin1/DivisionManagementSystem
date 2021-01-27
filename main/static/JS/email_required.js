function email_change () {
    let position_field = document.getElementById('id_position');
    let email_container = document.getElementById('div_id_email');
    let email_field = document.getElementById('id_email');


    if (position_field.options[position_field.selectedIndex].value === 'dispatcher') {
        email_container.style.display = 'block';
        email_field.required = true;
    } else {
        email_field.value = ''
        email_field.required = false;
        email_container.style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', function() {
   email_change();
}, false);