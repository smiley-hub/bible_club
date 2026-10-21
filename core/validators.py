import warnings

from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError


def validate_photo(value):
    """Validate actual image bytes, not just the filename or browser MIME type."""
    if value.size > 10 * 1024 * 1024:
        raise ValidationError('Please choose an image smaller than 10 MB.')
    try:
        value.open('rb')
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            image = Image.open(value)
            if image.format not in {'JPEG', 'PNG', 'WEBP'}:
                raise ValidationError('Please upload a JPEG, PNG, or WebP image.')
            if image.width * image.height > 24_000_000:
                raise ValidationError('Please choose an image with at most 24 megapixels.')
            image.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise ValidationError('Please upload a valid image.') from exc
    finally:
        value.seek(0)
