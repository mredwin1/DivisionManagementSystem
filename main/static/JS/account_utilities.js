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
        let delete_message = button.data('delete-message')

        $.each(button_data, function (key, value) {
            let id = '#' + key
            let element = $(id)
            element.text(value)
        })

        $('#primary_button').attr('href', primary_button_href)
        delete_button.attr('data-delete-url', secondary_button_href)
        delete_button.attr('data-delete-message', delete_message)
        $('#row4col1').attr('href', document_href)

    });
    $('.delete').click(function () {
        let delete_button = $(this)
        let message = delete_button.data('delete-message')
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