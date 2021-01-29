$(document).ready(function() {
    function upload(event) {
         $('#main').hide();
        $('#preloader').show();
        /* stop form from submitting normally */
        event.preventDefault();

        var data = new FormData($(this).get(0));
        console.log('Preloader')
        $.ajax({
           url: $(this).attr('action'),
           type: $(this).attr('method'),
           data: data,
           cache: false,
           processData: false,
           contentType: false,
           success: function (data) {
               location.href = data.url;
           },
           error: function (data) {
                $('#preloader').hide();
                $('#main').show();

                $.each(data.responseJSON, function (key, value) {
                    var id = '#id_' + key;
                    var parent = $(id).parent();
                    var p = $("<p>", {id: "error_1_id_" + key, "class": "invalid-feedback"});
                    var strong = $("<strong>").text(value);

                    if (key === 'action_type') {
                        if ($('#pd_check_override').length) {
                            $('#pd_check_override').show();
                        }
                    }

                    parent.find('p').remove();
                    p.append(strong);
                    parent.append(p);
                    p.show()
                });
           }
        });
        return false;
    }

    /* attach a submit handler to the form */
    $(function () {
        console.log($('form'));
        $('form').each(function() {
            $(this).submit(upload);
        });
    })
});
