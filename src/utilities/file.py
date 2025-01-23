import logging
import os
import uuid
from xml.dom.minidom import parse

from PIL import Image, ImageOps
from django.conf import settings
from django.contrib import messages
from django.core.files.storage import get_storage_class
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger("django.request")


def save_image_with_path(image, photo_name):
    """Generate a random filename. Uses DEFAULT_FILE_STORAGE to validate filename"""
    ext = os.path.splitext(photo_name)[1]

    image_path = f'images/{uuid.uuid4()}{ext}'

    fs = get_storage_class()()
    # Generate a new name if exists
    image_path = fs.get_available_name(image_path)

    image.save(os.path.join(settings.MEDIA_ROOT, image_path))

    return image_path


def crop_and_save(request, form, filefield, field_suffix=None, final_width=600, final_height=400):
    """
    Crop and save an image.
    :param filefield: FileField object name in request.FILES
    :param field_suffix: Form withImage, x, y, width, height field suffix identifiers
    :param final_width: final width to resize image
    :param final_height: final height to resize image
    """

    if field_suffix is None:
        field_suffix = ''

    original_image = request.FILES.get(filefield, False)
    with_image = form.cleaned_data.get(f'withImage{field_suffix}', False)

    if original_image:
        x = form.cleaned_data.get(f'x{field_suffix}')
        y = form.cleaned_data.get(f'y{field_suffix}')
        w = form.cleaned_data.get(f'width{field_suffix}')
        h = form.cleaned_data.get(f'height{field_suffix}')

        try:
            image = Image.open(original_image)
            # Fix image orientation based on EXIF information
            fixed_image = ImageOps.exif_transpose(image)

            cropped_image = image.crop((x, y, w + x, h + y))
            resized_image = cropped_image.resize((final_width, final_height), Image.LANCZOS)

            if cropped_image.width > fixed_image.width:
                size = (
                    abs(int((final_width - (final_width / cropped_image.width * fixed_image.width)) / 2)), final_height
                )
                white_background = Image.new(mode='RGBA', size=size, color=(255, 255, 255, 0))
                position = ((final_width - white_background.width), 0)
                resized_image.paste(white_background, position)
                position = (0, 0)
                resized_image.paste(white_background, position)

            if cropped_image.height > fixed_image.height:
                size = (
                    final_width,
                    abs(int((final_height - (final_height / cropped_image.height * fixed_image.height)) / 2))
                )
                white_background = Image.new(mode='RGBA', size=size, color=(255, 255, 255, 0))
                position = (0, (final_height - white_background.height))
                resized_image.paste(white_background, position)
                position = (0, 0)
                resized_image.paste(white_background, position)

            image_path = save_image_with_path(resized_image, original_image.name)
        except Exception as e:
            logger.exception(f'Error when trying to crop an resize image: {e}', extra={'request': request})
            messages.warning(request, _('There was an error adapting the image. Try with another image.'))
            image_path = ''
    elif with_image:
        image_path = '/'
    else:
        image_path = ''

    return image_path


def assign_image(image_filename, image_field, width=600, height=400):
    """
    Assigns and resizes an existing image to an ImageField. SVG images will be converted to png.
    :param image_filename: Relative image path
    :param image_field: ImageField instance
    :param width: Final image width
    :param height: Final image height
    """
    import cairosvg

    fs = get_storage_class()()

    if fs.exists(image_filename):
        image_path = fs.path(image_filename)
        file_path, file_ext = os.path.splitext(image_path)

        if file_ext.upper() == '.SVG':
            # Open svg file and set background color before convert to pgn
            svg_dom = parse(image_path)

            rect_element = svg_dom.createElement('rect')
            rect_element.setAttribute('width', '100%')
            rect_element.setAttribute('height', '100%')
            rect_element.setAttribute('fill', '#03301C')

            svg_element = svg_dom.documentElement

            first_child = svg_element.firstChild

            svg_element.insertBefore(rect_element, first_child)
            # Uses open to change svg. fs.save will generate a new file.
            with open(image_path, 'w') as f:
                f.write(svg_dom.toxml())

            new_image_path = f'{file_path}.png'

            cairosvg.svg2png(url=image_path, write_to=new_image_path)

            result_name = f'{os.path.splitext(image_filename)[0]}.png'
        else:
            result_name = image_filename

        image_field.name = result_name
        # Resize the image to the new size and replace original image
        with Image.open(image_field.path) as image:
            # Fix image orientation based on EXIF information
            fixed_image = ImageOps.exif_transpose(image)

            image_with, image_height = fixed_image.size

            if image_with < width or image_height < height:
                # Try to crop central region of image
                left = (image_with - width) // 2
                upper = (image_height - height) // 2
                right = (image_with + width) // 2
                lower = (image_height + height) // 2

                fixed_image = fixed_image.crop((left, upper, right, lower))

            resized_image = fixed_image.resize((width, height), Image.LANCZOS)
            resized_image.save(image_field.path)
    else:
        raise Exception(_('File %s does not exists') % image_filename)
