from io import BytesIO
from PIL import Image, ImageOps

class InvalidImage(Exception):
    pass

def decode_image(data: bytes, min_size: int = 16) -> Image.Image:
    try:
        with Image.open(BytesIO(data)) as src:
            src.verify()
        with Image.open(BytesIO(data)) as src:
            img = src.convert('RGBA')
    except Exception as exc:
        raise InvalidImage(str(exc)) from exc
    if img.width < min_size or img.height < min_size:
        raise InvalidImage(f'image too small: {img.size}')
    return img

def process_image(img: Image.Image, processing: str, size_mode: str = 'Original', custom_px: int = 512) -> Image.Image:
    if processing == 'Original' or size_mode == 'Original':
        return img
    target = custom_px if size_mode == 'Custom' else int(size_mode.split('x')[0])
    if target < 1:
        raise ValueError('Custom px must be positive')
    # Contain only. The image is never cropped or stretched.
    return ImageOps.contain(img, (target, target), method=Image.Resampling.LANCZOS)

def save_png(img: Image.Image, path):
    img.save(path, format='PNG', optimize=True)
