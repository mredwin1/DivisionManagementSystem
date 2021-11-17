$(document).ready(function(){
    $('#custom_list').click(function () {
        let form = $('#filter-form')
        let action = $(this).data('formaction')

        form.attr("action", action)
        form.attr("method", 'POST')

        form.submit()
    })
});