#!/usr/bin/env python
# coding: utf-8

import numpy as np
import cv2
from segment_anything import sam_model_registry,SamAutomaticMaskGenerator
import matplotlib.pyplot as plt 
import shutil 
import glob 
import os 
from PIL import Image
import easyocr
from core.config import global_params, settings
from typing import Tuple, List
import os
import subprocess
import shutil 

from core.segment_symbol.utils import calculate_iou, recognize_text,check_symbol_has_only_text,compare_images,find_closest_above_below


# Get the configured logger
logger = settings.configured_logger
offset = 3 
iou_threshold = 0.2
width_min = 2
width_max = 200 
hw_ratio = 0.01 
need_atleast_text_pixels = 50 
kernel_size = (3, 3)
min_image_size_again_get_text = 20


async def download_weightfile(file_url,save_path):
    try: 
        subprocess.run(["wget", "-O", save_path, file_url], check=True)
        return 200
    except Exception as ex:
        return f"Could not download the file: {ex}", 500
    
async def process_symbol(file, save_symbols_path) -> Tuple[str, int, List[np.ndarray]]:
    """
    Process an uploaded image file.

    This function reads the uploaded file, processes it, and returns a message and status code.

    Args:
    - file: An uploaded file object from FastAPI.

    Returns:
    - Tuple[str, int]: A message and HTTP status code.
    """

    device = global_params.sam_device
    model_type = global_params.sam_model["model_type"]
    checkpoint = global_params.sam_weight_path
    if(not os.path.exists(checkpoint)):
        file_download_status = await download_weightfile(global_params.sam_model["file_url"],
                                               global_params.sam_weight_path)
    try:
        # Try to load the model
        sam = sam_model_registry[model_type](checkpoint=checkpoint)
    except:
        # Issue might the file was not downloaded, lets do that first in any case. 
        file_download_status = await download_weightfile(global_params.sam_model["file_url"],
                                               global_params.sam_weight_path)
        sam = sam_model_registry[model_type](checkpoint=checkpoint)
               
    sam.to(device=device)
    filtered_final_symbols = []
    mask_generator = SamAutomaticMaskGenerator(
            model=sam,
            points_per_side=64, # 64
            pred_iou_thresh=0.9,
            stability_score_thresh=0.9,
            box_nms_thresh = 0.9,
            crop_nms_thresh = 0.9, 
            crop_n_layers=1,
            crop_n_points_downscale_factor=2,
            min_mask_region_area=0,
        )

    if(True):
        # Read the image file
        image_data = file.read()
        image_array = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        logger.info(f"Input image of size {image.shape}")
        masks = mask_generator.generate(image)
        logger.info(f"Obtained  {len(masks)} from segment anything")

        # Initialize variables
        all_symbols = []


        # First, extract all potential bboxes
        for i, mask in enumerate(masks):
            bbox = mask["bbox"]
            x, y, w, h = [int(i) for i in bbox]
            if(width_min <= w < width_max and width_min <= h < width_max and h/w > hw_ratio):
                roi = image[y-offset: y + h+offset, x-offset  : x + w+offset]
                all_symbols.append((roi, bbox))


        logger.info(f"Filtered based on size of bboxes {len(all_symbols)}")

        # Second, filter out bboxes based on IoU to remove dubplicates 
        filtered_symbols = []
        filtered_bboxes = []
        for i in range(len(all_symbols)):
            keep = True
            for j in range(len(all_symbols)):
                if i != j:
                    iou = calculate_iou(all_symbols[i][1], all_symbols[j][1])
                    if iou > iou_threshold:
                        # Keep the larger box
                        area_i = all_symbols[i][1][2] * all_symbols[i][1][3]
                        area_j = all_symbols[j][1][2] * all_symbols[j][1][3]
                        if area_i < area_j:
                            keep = False
                            break
            if keep:
                filtered_symbols.append(all_symbols[i][0])
                filtered_bboxes.append(all_symbols[i][1])


        logger.info(f"Filtered bboxes after IOU {len(filtered_bboxes)}")

        filtered_bboxes_without_text = []
        filtered_symbols_without_text = []
        for i, (bbox,symbol) in enumerate(zip(filtered_bboxes,filtered_symbols)):
            result , symbol_has_only_text = check_symbol_has_only_text(255-symbol[:,:,0])
            if(not symbol_has_only_text):
                filtered_bboxes_without_text.append(bbox)
                filtered_symbols_without_text.append(symbol)

        logger.info(f"Filtered bboxes after Removing only with text {len(filtered_symbols_without_text)}")

        above_below_bboxes = find_closest_above_below(filtered_bboxes_without_text)

        
        for idx,(bbox,symbol) in enumerate(zip(filtered_bboxes_without_text,filtered_symbols_without_text)):

            try:
                # Safe retrieval of 'above' and 'below' bounding box indices
                above_index = above_below_bboxes[idx]['above']
                below_index = above_below_bboxes[idx]['below']

                # Check if 'above' or 'below' is not None before accessing final_bboxes
                if above_index is not None:
                    above = filtered_bboxes_without_text[above_index]
                else:
                    above = None  # Or set to a default value that makes sense in your context

                if below_index is not None:
                    below = filtered_bboxes_without_text[below_index]
                else:
                    below = None  # Or set to a default value

                y_current, height_current = bbox[1], bbox[3]
                
                if above:
                    distance_above = (y_current - (above[1] + above[3]))//2
                    y_new = y_current - distance_above
                else:
                    y_new = y_current
                    distance_above = 0
                
                if below:
                    distance_below =( below[1] - (y_current + height_current))//2
                    # Adjust the height to extend halfway towards the below bbox
                    height_new = height_current + distance_below +distance_above
                else:
                    height_new = height_current +distance_above

                # Create the adjusted bbox with the new dimensions
                adjusted_bbox = [bbox[0], y_new, bbox[2], height_new]

                # Extract variables for convenience
                x, y, width, height = adjusted_bbox

                change_in_height = (height_new - bbox[3])
                #print(change_in_height)
                # Adjust the width by the same amount as the change in height
                xnew = bbox[0] - change_in_height//4
                width_new = bbox[2] + change_in_height//2
                #print(xnew, width_new)
                # Crop the image to the new bounding box
                y_start = int(y_new)
                y_end = int(y_new + height_new)
                x_start = int(xnew)
                x_end = int(xnew + width_new)

                # Crop the image using integer indices
                logger.info("Adjusted bboxes" , idx,y_start,y_end, x_start,x_end)
                new_cropped_image = image[y_start:y_end, x_start:x_end]
                final_symbol_image, percentage, id_symbol = compare_images(symbol, 
                                                                        new_cropped_image,
                                                                        image.shape)


                if(id_symbol==0): 
                    filtered_final_symbols.append(symbol)
                else:
                    filtered_final_symbols.append(new_cropped_image)
            except:
                filtered_final_symbols.append(symbol)
        logger.info(f"Detected symbols {len(filtered_final_symbols)}")
        return "Image processed successfully", 200,filtered_final_symbols
#    except Exception as ex:
#        return f"An error occurred: {ex}", 500, filtered_final_symbols