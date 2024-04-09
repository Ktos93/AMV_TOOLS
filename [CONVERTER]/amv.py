import argparse
import json
import numpy as np
import tifffile as tiff
import subprocess
import os

def convert_and_process(file_path):
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)

    images = []

    if isinstance(data, list):
        for two_d_array in data:
            image_data = np.array(two_d_array, dtype=np.float32)
            images.append(image_data)

        tiff.imwrite("output.tiff", np.array(images, dtype=np.float32))
        subprocess.run([
            'texconv.exe',
            '-f', 'R11G11B10_FLOAT',
            '-y',
            '-m', '1',
            'output.tiff'
        ])

        os.remove("output.tiff")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process JSON file and convert it to TIFF.")
    parser.add_argument("file", help="Path to the JSON file")
    args = parser.parse_args()

    convert_and_process(args.file)
