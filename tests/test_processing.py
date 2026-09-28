from PIL import Image
from app.image_processing import process_image

def test_original_preserves_size_and_aspect():
    img = Image.new('RGB',(600,300))
    out = process_image(img,'Original','Original')
    assert out.size == (600,300)

def test_contain_preserves_full_aspect():
    img=Image.new('RGB',(600,300))
    out=process_image(img,'Contain','512x512',512)
    assert out.size == (512,256)
