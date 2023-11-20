$(function() {
    /* Clear error fields when clicking */
    $('input').on('focus', function(){
        if($(this).is('.error'))
            $(this).removeClass('error');
    });
    $('select').on('focus', function(){
        if($(this).is('.error'))
            $(this).removeClass('error');
    });
    $('.select2-selection--multiple').on('focus', function(){
        if($(this).is('.error'))
            $(this).removeClass('error');
    });

    for(var instanceName in CKEDITOR.instances){
        CKEDITOR.instances[instanceName].on('focus', function(e){
            id='#cke_'+$(this).attr('name')
            if($(id).is('.error'))
                $(id).removeClass('error');
        })
    }





    /* form scripts */
    $('.submit').click(function(e){

        changeBtn(true);


        e.preventDefault()

        /* To check that we click on Save & continue  */
        if($(this).hasClass('continue'))
            var contin=true
        else
            var contin=false
        $('.myerror').remove()
        $.ajaxSettings.traditional = true;
        for(var instanceName in CKEDITOR.instances)
            CKEDITOR.instances[instanceName].updateElement();

        var form_id = $(this).parents('form:first').attr('id')
        var url = '/save'+form_id+'Ajax/'

        $.ajax({
            type: 'POST',
            url: url,
            processData: false,
            contentType: false,
            data: new FormData(document.getElementById(form_id)),
            success: function(response){
                if(contin){
                    $('#Id').val(response.Id)
                    $('.savedInfo').html('<span class="alert alert-success fade show">'+
                            '<i class="fas fa-check"></i> Saved</span>').show().fadeOut(2500)

                }else{
                        window.location.href = '/platform/'+response.Id+'?prev='+window.location.pathname
                }
                changeBtn(false);
            },
            error: function (response){
                if(response.status==500){
                    alert('Unexpected error, please contact with the administrator')
                }
                $.each(response.responseJSON, function(i,val){
                    $('#id_'+i).addClass('error')
                    $('#id_'+i).parent().find('.select2-selection--multiple').addClass('error')
                    $('#hint_id_'+i).append('<div class="myerror small text-danger">'+val+'</div>')
                    $('#cke_id_'+i).addClass('error')
                })
                $('html, body').animate({
                    scrollTop: $('.myerror:visible:first').offset().top-100
                }, 1000);
                changeBtn(false);
            }
       })

    })




})

function changeBtn (bool) {
    $("button.submit").attr('disabled', bool);
    $("button.submit.continue").attr('disabled', bool);
    $("button[type=submit]").attr('disabled', bool);
}
