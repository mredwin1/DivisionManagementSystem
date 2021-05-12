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
                            let id = '#id_' + key;
                            let parent = $(id).parent();
                            let p = $("<p>", {id: "error_1_id_" + key, "class": "invalid-feedback"});
                            let strong = $("<strong>").text(value);

                            if (key === 'action_type') {
                                let pd_check_override = $('#pd_check_override')
                                if (pd_check_override.length) {
                                    pd_check_override.show();
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
        $('form').each(function() {
            $(this).submit(upload);
        });
    })
});
