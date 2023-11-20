def easy_thumbnail_delete(**kwargs):
    from easy_thumbnails.files import get_thumbnailer
    file = kwargs['file']
    thumbnailer = get_thumbnailer(file)
    thumbnailer.delete_thumbnails()
