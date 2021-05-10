$(document).ready(function () {
    let other_canvas = document.getElementById('other_canvas')
    let manager_canvas = document.getElementById('manager_canvas')

    let other_signature_pad = new SignaturePad(other_canvas);
    let manager_signature_pad = new SignaturePad(manager_canvas);

    function resizeCanvas() {
        var ratio =  Math.max(window.devicePixelRatio || 1, 1);

        other_canvas.width = other_canvas.offsetWidth * ratio;
        other_canvas.height = other_canvas.offsetHeight * ratio;
        other_canvas.getContext("2d").scale(ratio, ratio);

        manager_canvas.width = manager_canvas.offsetWidth * ratio;
        manager_canvas.height = manager_canvas.offsetHeight * ratio;
        manager_canvas.getContext("2d").scale(ratio, ratio);

        other_signature_pad.clear();
        manager_signature_pad.clear();
    }

    window.onresize = resizeCanvas;
    resizeCanvas();

    $('.canvas-undo').click(function () {
        let canvas_type = $(this).data('canvas-type')
        let signaturePad = manager_signature_pad

        if (canvas_type === 'other') {
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
        let signaturePad = manager_signature_pad

        if (canvas_type === 'other') {
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
                console.log()
                if (data.signature) {
                    manager_signature_pad.clear()
                    manager_signature_pad.fromDataURL(data.signature)
                }
            },
        });
    })
    $('#submit_button').click(function () {
        let other_signature_data = other_signature_pad.toDataURL()
        let manager_signature_data = manager_signature_pad.toDataURL()

        let form = $('form')
        form.data('other-signature-data', other_signature_data)
        form.data('manager-signature-data', manager_signature_data)
        form.data('other-is-empty', other_signature_pad.isEmpty())
        form.data('manager-is-empty', manager_signature_pad.isEmpty())
    })
});