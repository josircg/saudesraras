import os
import uuid
from xml.dom.minidom import parse

from PIL import Image, ImageOps
from django.conf import settings
from django.core.files.storage import get_storage_class
from django.utils.translation import ugettext_lazy as _


def save_image_with_path(image, photo_name):
    """Generate a random filename. Uses DEFAULT_FILE_STORAGE to validate filename"""
    ext = os.path.splitext(photo_name)[1]

    image_path = f'images/{uuid.uuid4()}{ext}'

    fs = get_storage_class()()
    # Generate a new name if exists
    image_path = fs.get_available_name(image_path)

    image.save(os.path.join(settings.MEDIA_ROOT, image_path))

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
                left = (image_with - width) / 2
                upper = (image_height - height) / 2
                right = (image_with + width) / 2
                lower = (image_height + height) / 2

                fixed_image = fixed_image.crop((left, upper, right, lower))

            resized_image = fixed_image.resize((width, height), Image.LANCZOS)
            resized_image.save(image_field.path)
    else:
        raise Exception(_('File %s does not exists') % image_filename)
