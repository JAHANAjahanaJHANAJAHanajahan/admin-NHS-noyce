import os
import sys
import numpy as np
from PIL import Image, ImageOps, ImageFilter


def convert_image(image_path, output_path, threshold=220, upscale_factor=2, apply_sharpen=True):
    """
    Convert a dark-mode screenshot to a light-mode look, with some noise reduction:
      1. Invert colors.
      2. Force background to pure white using a luminance threshold.
      3. Optionally upscale the image for clarity (e.g., 2x).
      4. Optionally apply a sharpen filter to make text crisper.

    Args:
        image_path (str): Path to the input image.
        output_path (str): Path to the output (processed) image.
        threshold (int): Luminance threshold [0..255] for forcing pixels to white.
        upscale_factor (int): Factor by which to upscale the image (1 = no upscale).
        apply_sharpen (bool): Whether to apply a sharpen filter after upscaling.
    """
    try:
        with Image.open(image_path) as img:
            # 1) Ensure RGB
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # 2) Invert colors
            inverted_img = ImageOps.invert(img)

            # 3) Convert to NumPy array for thresholding
            img_array = np.array(inverted_img, dtype=np.uint8)

            # Calculate luminance for each pixel (0.299*R + 0.587*G + 0.114*B)
            luminance = 0.299 * img_array[..., 0] + 0.587 * img_array[..., 1] + 0.114 * img_array[..., 2]

            # Create a mask for pixels that are bright enough to be considered background
            mask = luminance >= threshold

            # Force those pixels to pure white
            img_array[mask] = [255, 255, 255]

            # 4) Convert back to PIL image
            processed_img = Image.fromarray(img_array)

            # 5) Optional: Upscale for clarity
            if upscale_factor > 1:
                width, height = processed_img.size
                new_size = (width * upscale_factor, height * upscale_factor)
                processed_img = processed_img.resize(new_size, resample=Image.LANCZOS)

            # 6) Optional: Sharpen the image
            if apply_sharpen:
                processed_img = processed_img.filter(ImageFilter.SHARPEN)

            # Save the result
            processed_img.save(output_path)
            print(f"Converted: {image_path} -> {output_path}")
    except Exception as e:
        print(f"Failed to process {image_path}: {e}")


def process_folder(input_folder, output_folder, threshold, upscale_factor, apply_sharpen):
    """
    Process all images in a given folder with the above conversion function.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Common image file extensions
    extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')

    found_any = False
    for file_name in os.listdir(input_folder):
        if file_name.lower().endswith(extensions):
            found_any = True
            input_path = os.path.join(input_folder, file_name)
            output_path = os.path.join(output_folder, file_name)
            convert_image(input_path, output_path, threshold, upscale_factor, apply_sharpen)

    if not found_any:
        print("No valid image files found in the folder.")


def main():
    print("=== Dark Mode to Light Mode Converter (Enhanced) ===")

    # Prompt for input folder
    input_folder = input("Enter the path to the folder containing dark mode screenshots: ").strip()
    if not os.path.isdir(input_folder):
        print("Invalid input folder path.")
        sys.exit(1)

    # Prompt for output folder
    output_folder = input("Enter the path to the folder where light mode images will be saved: ").strip()
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Prompt for luminance threshold (default 220)
    try:
        threshold_str = input("Enter the luminance threshold (0-255, default=220): ").strip()
        threshold = int(threshold_str) if threshold_str else 220
    except ValueError:
        print("Invalid threshold, using default of 220.")
        threshold = 220

    # Prompt for upscale factor (default 2)
    try:
        upscale_str = input("Enter the upscale factor (1=none, 2=2x, etc., default=2): ").strip()
        upscale_factor = int(upscale_str) if upscale_str else 2
        if upscale_factor < 1:
            upscale_factor = 1
    except ValueError:
        print("Invalid upscale factor, using default of 2.")
        upscale_factor = 2

    # Prompt for sharpen (Y/N)
    sharpen_str = input("Apply sharpen filter? (Y/N, default=Y): ").strip().lower()
    apply_sharpen = (sharpen_str != 'n')

    print(f"\nProcessing images in:\n  {input_folder}\nSaving converted images to:\n  {output_folder}")
    print(f"Luminance threshold = {threshold}, Upscale factor = {upscale_factor}, Sharpen = {apply_sharpen}\n")

    process_folder(input_folder, output_folder, threshold, upscale_factor, apply_sharpen)
    print("Conversion complete.")


if __name__ == '__main__':
    main()
