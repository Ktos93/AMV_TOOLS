import os
import numpy as np
from PIL import Image
import tifffile as tiff
import subprocess

from .xml import create_xml_file_reflection_probes

def load_png_files(folder_path):
    filenames = ['x-.png', 'x+.png', 'y-.png', 'y+.png', 'z-.png', 'z+.png']
    files = [os.path.join(folder_path, filename) for filename in filenames]
    return files

def png_to_array(png_file):
    image = Image.open(png_file)
    array = np.array(image, dtype=np.uint8)
    return array

def replace_white_with_alpha(array):

    if array.shape[2] == 3:
        alpha_channel = np.full((array.shape[0], array.shape[1], 1), 255, dtype=array.dtype)
        array = np.concatenate((array, alpha_channel), axis=2)

    white_color = np.array([128, 128, 128])
    tolerance = 10

    diff = np.abs(array[:, :, :3] - white_color)
    mask = np.all(diff <= tolerance, axis=-1)
    array[mask] = [0, 0, 0, 0]
    return array

def set_alpha_from_r(array, array_ao):
    if array.shape[2] == 3:
        alpha_channel = np.full((array.shape[0], array.shape[1], 1), 255, dtype=array.dtype)
        array = np.concatenate((array, alpha_channel), axis=2)
    alpha_channel = array_ao[:, :, 0]
    array[:, :, 3] = alpha_channel
    return array


def create_output_folder(start_path, uuid, size_name):
    folder_name = f"{uuid}{size_name}"
    output_folder_path = os.path.join(start_path, "output")
    texture_folder_path = os.path.join(output_folder_path, folder_name)
    if not os.path.exists(texture_folder_path):
        os.makedirs(texture_folder_path)
    return texture_folder_path



def convertRefProbes(start_path, uuid):

    sizes = {"_ul": (1024, 1024), "_hi": (512, 512), "_lo": (128, 128), "": (256, 256)}

    for folder_name in ["color", "normal", "depth"]:
        folder_path = os.path.join(start_path, folder_name)
        files = load_png_files(folder_path)
        images = []

        for file in files:
            if folder_name == "color":
                array = png_to_array(file)
                array = np.clip(array, 0, 255).astype(np.uint8)
                array_ao = png_to_array(os.path.join(start_path, "ao", os.path.basename(file))) * 0.5
                array = set_alpha_from_r(array, array_ao)
            elif folder_name == "depth":
                array = png_to_array(file)
            elif folder_name == "normal":
                array = png_to_array(file)
                array = replace_white_with_alpha(array)
            images.append(array)

        index = 'd' if folder_name == "depth" else ('0' if folder_name == "color" else '1')
        
        output_tiff = os.path.join(start_path, f"{uuid}_{index}.tiff")

        for size_name, size in sizes.items():
            if folder_name == "depth":
                resized_images = [Image.fromarray(image).resize(size, Image.LANCZOS) for image in images] 
               
                combined = []
                for image in resized_images:
                    white_image = np.full((size[0],size[1], 3), 255, dtype=np.uint8)
                    combined.append((white_image.astype(np.uint16) << 8) | np.array(image))

                tiff.imwrite(output_tiff, [np.array(image) for image in combined], dtype=np.uint16)
            else:
                resized_images = [Image.fromarray(image).resize(size, Image.LANCZOS) for image in images]
                tiff.imwrite(output_tiff, [np.array(image) for image in resized_images], dtype=np.uint8)
            output_folder = create_output_folder(start_path, uuid, size_name)
            addon_directory = os.path.dirname(__file__)
            texconv_path = os.path.join(addon_directory, "[CONVERTER]", "texconv.exe")

            args = [
                texconv_path,
                '-f', 'R16_UNORM' if folder_name == "depth" else ('BC3_UNORM_SRGB' if folder_name == "color" else 'BC3_UNORM'),
                '-y', 
                '-m', '1',
                '-o', output_folder,
            ]

            
            if folder_name == "color":
                args.append('-srgb')
            args.append(output_tiff)
            subprocess.run(args)
            os.remove(output_tiff)
            xml_ytd_filename = os.path.join(start_path, "output", f"{uuid}{size_name}.ytd.xml")
            create_xml_file_reflection_probes(xml_ytd_filename, uuid)

