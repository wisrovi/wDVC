# pylint: disable=E1101,R0914,W1514

"""
This module provides utilities for converting Pascal VOC XML annotations to YOLO format.

It includes functionality to parse XML files, calculate normalized bounding box 
coordinates (x_centre, y_centre, width, height) based on the source image dimensions, 
and map class names to specific identifiers using a configuration file.

The module can be executed as a script via the command line using the command found at the end.
"""

import os
import xml.etree.ElementTree as ET
from argparse import ArgumentParser

import cv2
import yaml
from tqdm import tqdm

DEFAULT_OUTPUT_FOLDER = "labels"


def _xyxy_to_yolo(
        xmin: int,
        ymin: int,
        xmax: int,
        ymax: int,
        filename: str
    ) -> tuple[float, float, float, float]:

    """
    Converts bounding box coordinates from XYXY format to YOLO format.

    Args:
        xmin (int): Minimum x-coordinate (top-left).
        ymin (int): Minimum y-coordinate (top-left).
        xmax (int): Maximum x-coordinate (bottom-right).
        ymax (int): Maximum y-coordinate (bottom-right).
        filename (str): Path to the image file to retrieve dimensions.

    Returns:
        tuple[float, float, float, float]: A tuple containing (x_centre, y_centre, width, height)
            normalized to the image dimensions.
    """

    image = cv2.imread(filename)
    image_height, image_width = image.shape[:2]

    x_centre = ((xmin + xmax) / 2) / image_width
    y_centre = ((ymin + ymax) / 2) / image_height

    width = (xmax - xmin) / image_width
    height = (ymax - ymin) / image_height

    return x_centre, y_centre, width, height


def convert_xml_to_txt(
        photos_folder: str,
        labels_folder: str,
        classes_file: str,
        output_folder: str
    ):

    """
    Parses XML annotations and converts them into YOLO format text files.

    This function reads Pascal VOC style XML files, maps class names to IDs based on a
    provided YAML file, and calculates normalized coordinates.

    Args:
        photos_folder (str): Directory containing the image files.
        labels_folder (str): Directory containing the XML annotation files.
        classes_file (str): Path to a YAML file mapping class IDs to class names.
        output_folder (str): Directory where the resulting .txt files will be saved.

    Raises:
        FileNotFoundError: If an image file referenced in the XML is not found in `photos_folder`.
        ValueError: If a class name found in an XML is not defined in the `classes_file`.
    """

    with open(classes_file) as file:
        classes: dict = yaml.safe_load(file)

    if output_folder == DEFAULT_OUTPUT_FOLDER:
        output_folder = os.path.join(os.path.dirname(photos_folder), DEFAULT_OUTPUT_FOLDER)

    os.makedirs(output_folder, exist_ok = True)

    photos = set(os.listdir(photos_folder))
    labels = os.listdir(labels_folder)
    for xml_file in tqdm(labels, total = len(labels), desc = "Generating labels:"):
        root = ET.parse(os.path.join(labels_folder, xml_file)).getroot()

        filename = root.find("filename").text
        if filename not in photos:
            raise FileNotFoundError(f"Photo {filename} not found for label '{xml_file}'")

        all_objects = []
        for member in root.findall("object"):
            bndbox = member.find("bndbox")
            xmin = int(bndbox.find("xmin").text)
            ymin = int(bndbox.find("ymin").text)
            xmax = int(bndbox.find("xmax").text)
            ymax = int(bndbox.find("ymax").text)

            identifier = None
            name = member.find("name").text
            for class_id, class_name in classes.items():
                if class_name == name:
                    identifier = class_id
                    break

            if identifier is None:
                raise ValueError(f"Class '{name}' was not found in \
                    '{classes_file}' for XML file '{xml_file}'")

            x_centre, y_centre, width, height = _xyxy_to_yolo(
                xmin = xmin,
                ymin = ymin,
                xmax = xmax,
                ymax = ymax,
                filename = os.path.join(photos_folder, filename)
            )

            all_objects.append(f"{identifier} {x_centre} {y_centre} {width} {height}")

        label_content = "\n".join(all_objects)

        filename, _ = os.path.splitext(filename)
        with open(os.path.join(output_folder, f"{filename}.txt"), "w") as file:
            file.write(label_content)


if __name__ == "__main__":
    # python -m src.scripts.data.xml_2_txt --photos_folder="" --labels_folder=""

    parser = ArgumentParser()
    parser.add_argument(
        "--photos_folder",
        type = str,
        required = True,
        help = "path to folder with JPG images"
    )
    parser.add_argument(
        "--labels_folder",
        type = str,
        required = True,
        help = "path to folder with XML files"
    )
    parser.add_argument(
        "--classes_file",
        type = str,
        default = "./src/scripts/data/classes.yml",
        help = "path to YAML file with classes"
    )
    parser.add_argument(
        "--output_folder",
        default = DEFAULT_OUTPUT_FOLDER,
        type = str,
        help = f"path to generated labels folder. \
            Defaults to <photos_folder>/../{DEFAULT_OUTPUT_FOLDER}"
    )

    args = vars(parser.parse_args())

    for folder_path in [args["photos_folder"], args["labels_folder"], args["classes_file"]]:
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder not found: '{folder_path}'")

    convert_xml_to_txt(
        photos_folder = args["photos_folder"],
        labels_folder = args["labels_folder"],
        classes_file = args["classes_file"],
        output_folder = args["output_folder"]
    )
