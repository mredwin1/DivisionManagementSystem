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
        let main_modal = $('#mainModal')
        let title = $('#mainModalTitle');

        title.text('Signature QR')
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
});