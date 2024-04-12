import argparse
import json
import numpy as np
import tifffile as tiff
import subprocess
import os
import sys

def convert_and_process(file_path):
    # Extracting directory and file name without extension
    
    directory = os.path.dirname(file_path)
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
   
    images = []

    if isinstance(data, list):
        for two_d_array in data:
            image_data = np.array(two_d_array, dtype=np.float32)
            images.append(image_data)

        output_tiff_path = os.path.join(directory, f"{file_name}.tiff")

        tiff.imwrite(output_tiff_path, np.array(images, dtype=np.float32))
        script_directory = ""

        if getattr(sys, 'frozen', False):
            script_directory = os.path.dirname(sys.executable)
        else:
            script_directory = os.path.dirname(os.path.realpath(__file__))

        texconv_path = os.path.join(script_directory, 'texconv.exe')    

        subprocess.run([
            texconv_path,
            '-f', 'R11G11B10_FLOAT',
            '-y',
            '-m', '1',
            '-o', directory,
            output_tiff_path
        ])

        os.remove(output_tiff_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process JSON file and convert it to TIFF.")
    parser.add_argument("file", help="Path to the JSON file")
    args = parser.parse_args()

    convert_and_process(args.file)
