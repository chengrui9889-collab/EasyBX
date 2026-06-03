from PIL import Image


def rotate_to_upright(image_path: str) -> str:
    img = Image.open(image_path)
    try:
        img = Image.open(image_path)
        exif = img._getexif()
        if exif:
            orientation = exif.get(0x0112, 1)
            if orientation == 3:
                img = img.rotate(180, expand=True)
            elif orientation == 6:
                img = img.rotate(270, expand=True)
            elif orientation == 8:
                img = img.rotate(90, expand=True)
            img.save(image_path)
    except Exception:
        pass
    return image_path
