import os
import numpy as np
import tifffile as tiff
import subprocess

from .xml import create_xml_file_reflection_probes

def load_png_files(folder_path):
    filenames = ['x-.tif', 'x+.tif', 'y-.tif', 'y+.tif', 'z-.tif', 'z+.tif']
    files = [os.path.join(folder_path, filename) for filename in filenames]
    return files

def png_to_array(png_file):
    with tiff.TiffFile(png_file) as tif:
        numpy_array = tif.asarray()
    return numpy_array

def replace_white_with_alpha(array):

    if array.shape[2] == 3:
        alpha_channel = np.full((array.shape[0], array.shape[1], 1), 65535, dtype=array.dtype)
        array = np.concatenate((array, alpha_channel), axis=2)

    white_color = np.array([32767, 32767, 32767])
    tolerance = 10

    diff = np.abs(array[:, :, :3] - white_color)
    mask = np.all(diff <= tolerance, axis=-1)
    array[mask] = [0, 0, 0, 0]
    return array

def set_alpha_from_r(array, array_ao):
    if array.shape[2] == 3:
        alpha_channel = np.full((array.shape[0], array.shape[1], 1), 65535, dtype=array.dtype)
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

                black_color = np.array([0, 0, 0])
                tolerance = 10
                diff = np.abs(array[:, :, :3] - black_color)
                mask = np.all(diff <= tolerance, axis=-1)
                max_value = (int(np.iinfo(array.dtype).max/2))
                array[mask] = [max_value, max_value, max_value]

                # array = np.clip(array, 0, 255).astype(np.uint8)
                array_ao = png_to_array(os.path.join(start_path, "ao", os.path.basename(file))) * 0.5

                black_color = np.array([0, 0, 0])
                tolerance = 10
                diff = np.abs(array_ao[:, :, :3] - black_color)
                mask = np.all(diff <= tolerance, axis=-1)
                max_value = np.iinfo(array.dtype).max
                array_ao[mask] = [max_value, max_value, max_value]

                array = set_alpha_from_r(array, array_ao)
            elif folder_name == "depth":
                array = png_to_array(file)
                array[array == max_value] = max_value - 10
            elif folder_name == "normal":
                array = png_to_array(file)
                array = replace_white_with_alpha(array)
            images.append(array)

        index = 'd' if folder_name == "depth" else ('0' if folder_name == "color" else '1')
        
        output_tiff = os.path.join(start_path, f"{uuid}_{index}.tiff")

        tiff.imwrite(output_tiff, [np.array(image) for image in images], dtype=np.uint16)

        for size_name, size in sizes.items():

            output_folder = create_output_folder(start_path, uuid, size_name)
            addon_directory = os.path.dirname(__file__)
            texconv_path = os.path.join(addon_directory, "[CONVERTER]", "texconv.exe")

            args = [
                texconv_path,
                '-f', 'R16_UNORM' if folder_name == "depth" else ('BC3_UNORM_SRGB' if folder_name == "color" else 'BC3_UNORM'),
                '-y', 
                '-w', str(size[0]),
                '-h', str(size[0]),
                '-m', '1',
                '-o', output_folder,
            ]

            
            if folder_name == "color":
                args.append('-srgb')
            args.append(output_tiff)
            subprocess.run(args)
            xml_ytd_filename = os.path.join(start_path, "output", f"{uuid}{size_name}.ytd.xml")
            create_xml_file_reflection_probes(xml_ytd_filename, uuid)
        os.remove(output_tiff)

