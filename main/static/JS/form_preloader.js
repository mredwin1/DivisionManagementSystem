$(document).ready(function() {
    function upload(event) {
        $('#main').hide();
        $('#preloader').show();
        /* stop form from submitting normally */
        event.preventDefault();

        let form = $(this)
        let other_signature = $('#other_signature')
        let manager_signature = $('#manager_signature')
        let form_data = new FormData(form.get(0));

        if (manager_signature || other_signature) {
            let other_signature_data = form.data('other-signature-data')
            let manager_signature_data = form.data('manager-signature-data')
            let other_is_empty = form.data('other-is-empty')
            let manager_is_empty = form.data('manager-is-empty')

            if (manager_is_empty) {
                let container = $('#manager_container');
                let p = $("<p>", {id: "error_1_manager_canvas", "class": "invalid-feedback m-0"});
                let strong = $("<strong>").text('This signature cannot be blank');

                container.find('#error_1_manager_canvas').remove();
                p.append(strong);
                container.append(p);
                p.show()

                $('#preloader').hide();
                $('#main').show();
            } else {
                console.log(other_is_empty)
                if (!other_is_empty){
                    form_data.append('other_signature', other_signature_data)
                }
                form_data.append('manager_signature', manager_signature_data)
                $.ajax({
                    url: form.attr('action'),
                    type: form.attr('method'),
                    data: form_data,
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

        }
    }

    /* attach a submit handler to the form */
    $(function () {
        $('form').each(function() {
            $(this).submit(upload);
        });
    })
});
