import os
from PIL import Image
import numpy as np 
import shutil 
from core.config import global_params, settings
import logging

logger = settings.configured_logger
logger_active = logging.getLogger().isEnabledFor(logging.INFO)

def split_image_into_sections(image, image_name, section_size=(1900, 1700)):
    """
    Splits an image into sections of specified size and saves the sections.

    This function divides a given image into smaller sections based on the specified section size. Each section is saved as a separate image file. The function also generates a list of these sections and their corresponding locations in the original image.

    Args:
    - image (numpy.ndarray): The image to be split, in the form of a numpy array.
    - image_name (str): The name of the original image. This is used to create the folder structure for saving sections.
    - section_size (tuple): A tuple (width, height) specifying the size of each section. Default is (1900, 1700).

    Returns:
    - list: A list of numpy arrays, each representing a section of the original image.
    - str: The path to the directory where the image sections are saved.
    - list: A list of tuples, each containing the (y1, y2) and (x1, x2) coordinates of the corresponding section in the original image. This is needed to put sections together
    """
    sections = []
    locations = []
    x_step, y_step = section_size
    y_max, x_max, _ = image.shape
    x_step = min(x_step,x_max) # Handle images of lower size than the section 
    y_step = min(y_step,y_max)

    save_sections_path = ""
    if(logger_active):
        image_name = os.path.splitext(image_name)[0]
        save_sections_path = f'temp/sections/{image_name}'
        try: 
            shutil.rmtree(save_sections_path) # Delete the path 
        except:
            pass 
        os.makedirs(save_sections_path, exist_ok=True)

    count = 0 
    for y in range(0, y_max, y_step):
        for x in range(0, x_max, x_step):
            y_end = min(y + y_step, y_max)
            x_end = min(x + x_step, x_max)
            section = image[y:y_end, x:x_end]
            sections.append(section)
            if(logger_active):
                Image.fromarray(section).save(f'{save_sections_path}/section_{count}.jpg')
            count+=1
            locations.append([(y, y_end), (x, x_end)])
    return save_sections_path, sections, locations

def patch_sections_together(sections, original_size, locations):
    """
    Reconstructs an image from its section arrays.

    This function takes a list of image sections (as numpy arrays) and stitches them
    together to recreate the original image.

    Args:
    - sections (list): A list of numpy arrays representing the image sections.
    - original_size (tuple): The size of the original image (width, height).
    - section_size (tuple): The size of each section (width, height). 

    Returns:
    - Image: The reconstructed complete image.
    """

    complete_image = np.zeros((original_size[0], original_size[1], 3), dtype=np.uint8) + 255
    for i in range(len(sections)):
        location = locations[i]
        (x1,x2), (y1,y2) = location
        complete_image[x1:x2,y1:y2]=sections[i]
            
    return complete_image

def adjust_bounding_boxes(processed_boxes, locations):
    """
    Adjust bounding boxes from sections to the complete image.

    Parameters:
    - processed_boxes (list): Nested list of bounding boxes for each section.
    - locations (list): List of tuples indicating the locations of each section in the original image.

    Returns:
    - list: Adjusted bounding boxes for the complete image.
    """
    adjusted_boxes = []

    for section_index, section_boxes in enumerate(processed_boxes):
        # Get the offset for the current section from the locations list
        (y1, y2), (x1, x2) = locations[section_index]

        for box in section_boxes:
            # Adjust each box
            (bx1, by1), (bx2, by2) = box
            adjusted_box = ((bx1 + x1, by1 + y1), (bx2 + x1, by2 + y1))
            adjusted_boxes.append(adjusted_box)

    return adjusted_boxes
