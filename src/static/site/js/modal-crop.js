/*
 This code uses cropper.js in a bootstrap modal
 Depends on jquery, jquery-ui, jquery.ui.touch-punch, cropper, jquery-cropper and _crop_zone.html
*/
(function ($) {
    $(document).ready(function () {
        // Current input file
        let $imgSelected;
        // Option to define cropper width: 0 = 600 x 400 - 1 = 1100 x 400
        let imgWidthOption;
        // Inputs defined on _crop_zone.html
        let $image = $("#image");
        let $modalCrop = $("#modalCrop");
        let $zoomSlider = $("#zoom-slider");
        // Inputs that hold information about original image and cropped image result
        let $images = $('.fileinput');

        $images.each(function () {
            // Binds on change function to each input target marked as image result
            $('#imageResult' + $(this).data('image-suffix')).click(function () {
                $modalCrop.modal("show");
            });
        });
        // SCRIPT TO OPEN THE MODAL WITH THE PREVIEW
        $images.change(function () {
            $imgSelected = $(this);
            imgWidthOption = $imgSelected.data('image-width-option');

            if (this.files && this.files[0]) {
                let reader = new FileReader();
                reader.onload = function (e) {
                    $image.attr("src", e.target.result);
                    $modalCrop.modal("show");
                }
                reader.readAsDataURL(this.files[0]);
            }
        });

        // SCRIPTS TO HANDLE THE CROPPER BOX
        $modalCrop.on("shown.bs.modal", function () {
            let cropBoxData;
            let canvasData;
            $zoomSlider.val(0);

            $image.cropper({
                viewMode: 1,
                aspectRatio: imgWidthOption === 1 ? 11 / 4 : 3 / 2,
                minCropBoxWidth: imgWidthOption === 1 ? 1100 : 600,
                minCropBoxHeight: 400,
                dragMode: 'move',
                guides: false,
                center: false,
                highlight: false,
                cropBoxResizable: false,
                toggleDragModeOnDblclick: false,
                zoomOnTouch: false,
                zoomOnWheel: false,
                ready: function (e) {
                    $image.cropper("setCanvasData", canvasData)
                        .cropper("setCropBoxData", cropBoxData)
                        .cropper('zoomTo', 0);

                    let imageData = $image.cropper('getImageData');

                    console.log("imageData ", imageData);

                    let minSliderZoom = imageData.width / imageData.naturalWidth;

                    $(".cr-slider-wrap").show();

                    $zoomSlider.slider("option", "max", 1)
                        .slider("option", "min", minSliderZoom)
                        .slider("value", minSliderZoom);
                }
            });
        }).on("hidden.bs.modal", function () {
            cropBoxData = $image.cropper("getCropBoxData");
            canvasData = $image.cropper("getCanvasData");
            $image.cropper("destroy");
        });

        $zoomSlider.slider({
            orientation: "horizontal",
            range: "min",
            max: 1,
            min: 0,
            value: 0,
            step: 0.0001,
            slide: function (event) {
                let canvasData = $image.cropper("getCanvasData");

                if (canvasData.naturalWidth < 600 || canvasData.naturalHeight < 400) {
                    event.preventDefault();
                } else {
                    let currentValue = $zoomSlider.slider("value");
                    let zoomValue = parseFloat(currentValue);
                    $image.cropper('zoomTo', zoomValue.toFixed(4));
                }
            }
        });

        // SCRIPT TO COLLECT THE DATA AND POST TO THE SERVER
        $(".js-crop-and-upload").click(function () {
            let cropData = $image.cropper("getData");
            let suffix = $imgSelected.data('image-suffix');
            $("#id_x" + suffix).val(cropData["x"]);
            $("#id_y" + suffix).val(cropData["y"]);
            $("#id_height" + suffix).val(cropData["height"]);
            $("#id_width" + suffix).val(cropData["width"]);

            $modalCrop.modal("hide");

            $('#imageResult' + suffix).attr('src', $image.cropper('getCroppedCanvas',
                {width: imgWidthOption === 1 ? 1100 : 600, height: 400}).toDataURL());
        });
    });
})(jQuery);