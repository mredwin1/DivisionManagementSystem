$(document).ready(function(){
    $('#comments_btn').click(function () {
        let comments_container = $('#comments_container')

        if (comments_container.is(':visible')) {
            comments_container.hide()
        } else {
            comments_container.show()
        }
    })
});