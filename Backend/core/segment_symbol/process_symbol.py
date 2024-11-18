import torch
import numpy as np
import cv2
from segment_anything import sam_model_registry,SamAutomaticMaskGenerator
from core.config import global_params
import os
from typing import Tuple, List
import io
import os
import subprocess
import shutil 

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
    mask_generator = SamAutomaticMaskGenerator(
        model=sam,
        points_per_side=32,
        pred_iou_thresh=0.86,
        stability_score_thresh=0.92,
        crop_n_layers=1,
        crop_n_points_downscale_factor=2,
        min_mask_region_area=400,
    )
    symbols_generated = []
    try:
        # Read the image file
        image_data = await file.read()
        image_array = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        file_paths = []
        try: 
            shutil.rmtree(save_symbols_path)
        except:
            pass 
        os.makedirs(save_symbols_path, exist_ok=True)

        masks = mask_generator.generate(image)

        for i, mask in enumerate(masks):
            bbox = mask["bbox"]
            x, y, w, h = [int(i) for i in bbox]
            # Define the minimum and maximum dimensions allowed for ROIs
            min_width, min_height = global_params.sam_min_width, global_params.sam_min_width
            max_width, max_height = global_params.sam_max_width, global_params.sam_max_width

            #Check if the ROI dimensions are within the allowed range
            if not (min_width <= w <= max_width and min_height <= h <= max_height):
                continue
            roi = image[y : y + h, x : x + w]
            if roi.size == 0:
                continue
            # save the ROI
            file_path = f"{save_symbols_path}/symbol{i}.jpg"
            cv2.imwrite(file_path, cv2.cvtColor(roi, cv2.COLOR_RGB2BGR))
            file_paths.append(file_path)
            symbols_generated.append(roi)
            print(roi.shape)
        return "Image processed successfully", 200,symbols_generated
    except Exception as ex:
        return f"An error occurred: {ex}", 500