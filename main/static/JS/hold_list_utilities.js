$(document).ready(function () {
    $('.edit-hold').click(function () {
        let modal = $('#mainModal');
        let form = $('#editEmployeeHoldForm');
        let account_button = $('#accountButton');
        let title = $('#mainModalTitle');
        let reason_field = $('#id_reason');
        let reason_options = reason_field.map(function() { return $(this).val(); });
        let other_reason_container = $('#div_id_other_reason');
        let other_reason_field = $('#id_other_reason');
        let incident_date_field = $('#id_incident_date');
        let release_date_field = $('#id_release_date');
        let training_date_field = $('#id_training_date');
        let training_time_field = $('#id_training_time');
        let form_url = $(this).data('submit-url')
        let employee_url = $(this).data('employee-url')
        let name = $(this).data('name')
        let title_text = 'Edit ' + name + '\'s Hold'
        let reason = $(this).data('reason')
        let incident_date = $(this).data('incident-date')
        let release_date = $(this).data('release-date')
        let training_datetime = $(this).data('training-datetime')

        form.attr('action', form_url)
        account_button.attr('href', employee_url)

        if (reason in reason_options) {
            reason_field.val(reason)
            other_reason_field.prop('required', false)
            other_reason_container.hide();
        } else {
            reason_field.val('Other')
            other_reason_field.val(reason)
            other_reason_field.prop('required', true)
            other_reason_container.show()
        }
        if (incident_date) {
            let incident_month = incident_date.substring(0, incident_date.indexOf('-'))
            let incident_day = incident_date.substring(incident_date.indexOf('-') + 1, incident_date.lastIndexOf('-'))
            let incident_year = incident_date.substring(incident_date.lastIndexOf('-') + 1, incident_date.length)
            let formatted_incident_date = incident_year + '-' + incident_month + '-' + incident_day
            
            incident_date_field.val(formatted_incident_date)
        }
        if (release_date) {
            let release_month = release_date.substring(0, release_date.indexOf('-'))
            let release_day = release_date.substring(release_date.indexOf('-') + 1, release_date.lastIndexOf('-'))
            let release_year = release_date.substring(release_date.lastIndexOf('-') + 1, release_date.length)
            let formatted_release_date = release_year + '-' + release_month + '-' + release_day

            release_date_field.val(formatted_release_date)
        }
        if (training_datetime) {
            let index = training_datetime.indexOf('@')
            let training_date = training_datetime.substring(0, index - 1)
            let training_time = training_datetime.substring(index + 2, training_datetime.length)
            let training_month = training_date.substring(0, training_date.indexOf('-'))
            let training_day = training_date.substring(training_date.indexOf('-') + 1, training_date.lastIndexOf('-'))
            let training_year = training_date.substring(training_date.lastIndexOf('-') + 1, training_date.length)
            let training_hour = (parseInt(training_time.substring(0, training_time.indexOf(':'))) + 12).toString()
            let training_minute = training_time.substring(training_time.indexOf(':') + 1, training_time.indexOf(' '))
            let formatted_training_date = training_year + '-' + training_month + '-' + training_day
            let formatted_training_time = training_hour + ':' + training_minute

            training_date_field.val(formatted_training_date)
            training_time_field.val(formatted_training_time)
        }

        title.text(title_text);
        modal.modal('show');
    });
    $('#editEmployeeHoldForm').submit(function (event) {
        event.preventDefault();

        let form = $(this);
        let main_modal = $('#mainModal');
        let data = new FormData(form.get(0));

        $.ajax({
            url: form.attr('action'),
            type: form.attr('method'),
            data: data,
            cache: false,
            processData: false,
            contentType: false,
            success: function (data) {
                main_modal.modal('hide');
                location.reload()
            },
            error: function (data) {
                $.each(data.responseJSON, function (key, value) {
                    var id = '#id_' + key;
                    var parent = $(id).parent();
                    var p = $("<p>", {id: "error_1_id_" + key, "class": "invalid-feedback"});
                    var strong = $("<strong>").text(value);

                    parent.find('p').remove();
                    p.append(strong);
                    parent.append(p);
                    p.show();
                });
            }
        });
    });
    $('#id_reason').change(function () {
        let reason_field = document.getElementById('id_reason');
        let other_reason_container = document.getElementById('div_id_other_reason');
        let other_reason_field = document.getElementById('id_other_reason');

        if (reason_field.options[reason_field.selectedIndex].value === 'Other') {
            other_reason_container.style.display = 'block';
            other_reason_field.required = true;
        } else {
            other_reason_field.value = ''
            other_reason_field.required = false;
            other_reason_container.style.display = 'none';
        }
    })
});
