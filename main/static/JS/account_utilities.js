$(document).ready(function(){
    $("#mainModal").on('show.bs.modal', function(event){
        let button = $(event.relatedTarget); // Button that triggered the modal
        let button_data = button.data()
        let primary_button_href = button.data('primary-href')
        let secondary_button_href = button.data('secondary-href')
        let document_href = button.data('document-href')
        let signature_href = button.data('signature-href')
        let signature_button = $('#signature_button')

        $.each(button_data, function (key, value) {
            let id = '#' + key
            let element = $(id)
            element.text(value)
        })

        $('#primary_button').attr('href', primary_button_href)
        $('#secondary_button').attr('href', secondary_button_href)
        $('#row4col1').attr('href', document_href)

        if (signature_href === '') {
            signature_button.removeClass('btn-primary')
            signature_button.addClass('disabled')
            signature_button.addClass('btn-secondary')
        } else {
            signature_button.removeClass('disabled')
            signature_button.removeClass('btn-secondary')
            signature_button.addClass('btn-primary')
            signature_button.attr('href', signature_href)
        }


    });
    $('#secondaryButton').click(function () {
        return confirm('Are you sure you would like to delete this record?')
    })
});