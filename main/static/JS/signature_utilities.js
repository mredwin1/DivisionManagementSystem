$(document).ready(function () {
    $.getScript($('#qr_script').data('src'))

    let other_canvas = document.getElementById('other_canvas')
    let manager_canvas = document.getElementById('manager_canvas')
    let other_signature_pad = null
    let manager_signature_pad = null

    if (other_canvas){
        other_signature_pad = new SignaturePad(other_canvas);
    }

    if (manager_canvas) {
        manager_signature_pad = new SignaturePad(manager_canvas);
    }

    function resizeCanvas() {
        var ratio =  Math.max(window.devicePixelRatio || 1, 1);
        if (other_canvas) {
            other_canvas.width = other_canvas.offsetWidth * ratio;
            other_canvas.height = other_canvas.offsetHeight * ratio;
            other_canvas.getContext("2d").scale(ratio, ratio);

            other_signature_pad.clear();
        }

        if (manager_canvas) {
            manager_canvas.width = manager_canvas.offsetWidth * ratio;
            manager_canvas.height = manager_canvas.offsetHeight * ratio;
            manager_canvas.getContext("2d").scale(ratio, ratio);

            manager_signature_pad.clear();
        }
    }

    window.onresize = resizeCanvas;
    resizeCanvas();

    $('.canvas-undo').click(function () {
        let canvas_type = $(this).data('canvas-type')
        let signaturePad = null

        if (canvas_type === 'manager') {
            signaturePad = manager_signature_pad
        } else {
            signaturePad = other_signature_pad
        }


        let data = signaturePad.toData();

        if (data) {
            data.pop(); // remove the last dot or line
            signaturePad.fromData(data);
        }
    })
    $('.canvas-clear').click(function () {
        let canvas_type = $(this).data('canvas-type')
        let signaturePad = null

        if (canvas_type === 'manager') {
            signaturePad = manager_signature_pad
        } else {
            signaturePad = other_signature_pad
        }

        signaturePad.clear()
    })
    $('.canvas-load').click(function () {
        $.ajax({
            url: $(this).data('signature-url'),
            type: 'GET',
            cache: false,
            processData: false,
            contentType: false,
            success: function (data) {
                if (data.signature) {
                    if (manager_canvas) {
                        manager_signature_pad.clear()
                        manager_signature_pad.fromDataURL(data.signature)
                    }
                }
            },
        });
    })
    $('.canvas-qr').click(function () {
        let qr_url = $(this).data('qr-url')
        let canvas_type = $(this).data('canvas-type')
        let main_modal = $('#mainModal')
        let title = $('#mainModalTitle');

        if (canvas_type === 'other') {
            title.text('Signature QR')
            $.ajax({
                url: $(this).data('clear-url'),
                type: 'GET',
                cache: false,
                processData: false,
                contentType: false,
            });
        } else {
            title.text('Manager Signature QR')
        }


        $("#qr").ClassyQR({
            type: 'url',
            url: qr_url
        });

        main_modal.modal('show')

    })
    $('#submit_button').click(function () {
        let form = $('form')
        if (manager_canvas) {
            let manager_signature_data = manager_signature_pad.toDataURL()
            form.data('manager-signature-data', manager_signature_data)
            form.data('manager-is-empty', manager_signature_pad.isEmpty())
        }

        if (other_canvas) {
            let other_signature_data = other_signature_pad.toDataURL()
            form.data('other-signature-data', other_signature_data)
            form.data('other-is-empty', other_signature_pad.isEmpty())
        }
    })
    $('#id_refused_to_sign').click(function () {
        let other_signature_title = $('#other_signature_title')
        let other_qr = $('#other_qr')
        let form = $('form')
        let signature_method = form.data('signature-method')
        let refused_to_sign = $(this)

        if (signature_method === 'In Person' || signature_method === 'Self Service' ) {
            if (refused_to_sign.prop('checked')) {
                other_signature_title.text('Witness Signature*')
                other_qr.hide()
            } else {
                other_signature_title.text('Employee Signature*')
                other_qr.show()
            }
        } else if (form.data('signature-method') === '') {
            if (refused_to_sign.prop('checked')) {
                other_signature_title.text('Witness Signature*')
                form.data('other-required', true)
                other_qr.hide()
            } else {
                other_signature_title.text('Employee Signature')
                form.data('other-required', false)
                other_qr.show()
            }
        }
    })
    $('#mainModal').on('hidden.bs.modal', function (e) {
        let title = $('#mainModalTitle').text()
        let signaturePad = null
        let signature_method = $('#signature_method')
        let qr_button = $('#other_qr')

        if (title.indexOf('Manager') === -1) {
            signaturePad = other_signature_pad
        } else {
            signaturePad = manager_signature_pad
        }

        $.ajax({
            url: qr_button.data('signature-url'),
            type: 'GET',
            cache: false,
            processData: false,
            contentType: false,
            success: function (data) {
                if (data.signature) {
                    signaturePad.clear()
                    signaturePad.fromDataURL(data.signature)
                    if (title.indexOf('Manager') === -1) {
                        signature_method.val('QR')
                    }
                }
            },
        });
        if (title.indexOf('Manager') === -1) {
            $.ajax({
                url: qr_button.data('clear-url'),
                type: 'GET',
                cache: false,
                processData: false,
                contentType: false,
            });
        }
    })
});