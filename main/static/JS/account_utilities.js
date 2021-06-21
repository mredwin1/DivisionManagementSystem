$(document).ready(function(){
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    $("#mainModal").on('show.bs.modal', function(event){
        let button = $(event.relatedTarget); // Button that triggered the modal
        let delete_button =$('#mainModal').find('.delete');
        let button_data = button.data()
        let primary_button_href = button.data('primary-href')
        let secondary_button_href = button.data('secondary-href')
        let document_href = button.data('document-href')
        let signature_href = button.data('signature-href')
        let simple_signature_href = button.data('simple-signature-href')
        let delete_message = button.data('delete-message')
        let signature_button = $('#signature_button')
        let values = []

        $.each(button_data, function (key, value) {
            let id = '#' + key
            let element = $(id)
            element.text(value)
            values.push(value)
        })

        if (values.includes('Time Off Request')) {
            signature_button.hide()
        } else {
            signature_button.show()
        }

        $('#primary_button').attr('href', primary_button_href)
        delete_button.attr('data-delete-url', secondary_button_href)
        delete_button.attr('data-delete-message', delete_message)
        $('#row4col1').attr('href', document_href)

        if (signature_href === '' && (simple_signature_href === '' || simple_signature_href === undefined)) {
            signature_button.text('Sign Document')
            signature_button.removeClass('btn-primary')
            signature_button.addClass('disabled')
            signature_button.addClass('btn-secondary')
        } else if (signature_href === '' && (simple_signature_href !== undefined && simple_signature_href !== '')) {
            signature_button.text('Add Employee Signature')
            signature_button.removeClass('disabled')
            signature_button.removeClass('btn-secondary')
            signature_button.addClass('btn-primary')
            signature_button.attr('href', simple_signature_href)
        } else {
            signature_button.text('Sign Document')
            signature_button.removeClass('disabled')
            signature_button.removeClass('btn-secondary')
            signature_button.addClass('btn-primary')
            signature_button.attr('href', signature_href)
        }
    });
    $('.delete').click(function () {
        let delete_button = $(this)
        let message = delete_button.data('delete-message')
        console.log(message)
        if (confirm(message)) {
            let delete_url = delete_button.data('delete-url')
            $.ajax({
                url: delete_url,
                type: 'POST',
                cache: false,
                headers: { "X-CSRFToken": getCookie("csrftoken") },
                processData: false,
                contentType: false,
                success: function (data) {
                    location.reload()
                },
                error: function (data) {

                }
            });
        }
    })
});