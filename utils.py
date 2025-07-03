
from PIL import Image
import os

def resize_image(input_path, output_path, size):
    """
    Resizes an image to the specified size, maintaining aspect ratio
    by adding transparent letterboxing (padding).
    """
    try:
        with Image.open(input_path) as img:
            img = img.convert("RGBA")

            target_width, target_height = size
            target_ratio = target_width / target_height
            img_ratio = img.width / img.height

            if img_ratio > target_ratio:
                new_width = target_width
                new_height = int(new_width / img_ratio)
            else:
                new_height = target_height
                new_width = int(new_height * img_ratio)

            # For compatibility with older Pillow versions
            resample_filter = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
            resized_img = img.resize((new_width, new_height), resample_filter)

            background = Image.new("RGBA", size, (255, 255, 255, 0))
            paste_x = (target_width - new_width) // 2
            paste_y = (target_height - new_height) // 2
            background.paste(resized_img, (paste_x, paste_y))

            background.save(output_path, "PNG")
        return True
    except Exception as e:
        print(f"Error resizing image: {e}")
        return False
