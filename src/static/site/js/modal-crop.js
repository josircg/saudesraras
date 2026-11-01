/*
 This code uses cropper.js in a bootstrap modal
 Depends on jquery, jquery-ui, jquery.ui.touch-punch, cropper, jquery-cropper and _crop_zone.html
*/
(function ($) {
    $(document).ready(function () {
        // Current input file
        let $imgSelected;
        // Option to define cropper size (data-image-width-option):
        // 0 = 600 x 400 (3:2), 1 = 1100 x 400 (11:4), 2 = 600 x 848 (A4 retrato, 210:297)
        let imgWidthOption;
        const CROP_PRESETS = {
            0: {width: 600, height: 400},
            1: {width: 1100, height: 400},
            2: {width: 600, height: 848},
        };
        function cropPreset() {
            return CROP_PRESETS[imgWidthOption] || CROP_PRESETS[0];
        }
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
            let preset = cropPreset();

            $image.cropper({
                viewMode: 1,
                aspectRatio: preset.width / preset.height,
                minCropBoxWidth: preset.width,
                minCropBoxHeight: preset.height,
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
                let preset = cropPreset();

                if (canvasData.naturalWidth < preset.width || canvasData.naturalHeight < preset.height) {
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

            let preset = cropPreset();
            $('#imageResult' + suffix).attr('src', $image.cropper('getCroppedCanvas',
                {width: preset.width, height: preset.height}).toDataURL());
        });
    });
})(jQuery);