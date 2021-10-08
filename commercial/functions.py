import logging
from io import BytesIO
from django.template import loader
from PIL import Image
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)

def export_to_csv(request, order, encode):
    return loader.render_to_string('commercial/csv.html', {'order': order})

def get_thumbnail_url(image, size):
    thumb_name = image.name.replace('upload/foto', 'thumb/{}'.format(size))
    logger.debug('get_thumbnail_url: %s %s', image.name, thumb_name)
    image_bytes = BytesIO()

    if not default_storage.exists(image.name):
        logger.debug('%s does not exit', image.name)
        return '#'

    if not default_storage.exists(thumb_name):
        logger.debug('%s does not exit', thumb_name)
        thumb = Image.open(default_storage.open(image.name))
        try:
            thumb.thumbnail((int(size), int(size)), Image.ANTIALIAS)
        except IOError:
            thumb = Image.new("RGB", (1, 1), (255, 255, 255))
        finally:
            thumb = thumb.convert('RGB')
            thumb.save(image_bytes, "JPEG")
            thumb_name = default_storage.save(thumb_name, ContentFile(image_bytes.getvalue()))
    elif default_storage.modified_time(image.name) > default_storage.modified_time(thumb_name):
        default_storage.delete(thumb_name)
        thumb = Image.open(default_storage.open(image.name))
        thumb.thumbnail((int(size), int(size)), Image.ANTIALIAS)
        thumb = thumb.convert('RGB')
        thumb.save(image_bytes, "JPEG")
        thumb_name = default_storage.save(thumb_name, ContentFile(image_bytes.getvalue()))
    thumb_url = default_storage.url(thumb_name)
    logger.debug('Thumb url: %s', thumb_url)
    return thumb_url
