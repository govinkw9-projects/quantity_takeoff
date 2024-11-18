import torch
import numpy as np
import cv2
from segment_anything import sam_model_registry,SamAutomaticMaskGenerator
import os
from typing import Tuple
import io
import os
import subprocess
import shutil 


class GlobalParams():
    threshold = 0.80 
    nms_threshold = 0.5 
    run_in_parallel = True # Always true, just adjust the number of workers. 
    max_workers = 1
    image_similarity_threshold = 0.7
    image_similarity_imgsize = (32,32)
    image_similarity_weight_file = "core/template_similarity/onnx_weights/siamese_network.onnx"
    section_size = (1900, 1500)
    degrees = [0]

    # Visualization 
    color_lists = [
                    (255, 0, 0),    # Red
                    (0, 255, 0),    # Green
                    (0, 0, 255),    # Blue
                    (255, 255, 0),  # Yellow
                    (0, 255, 255),  # Cyan
                    (255, 0, 255),  # Magenta
                    (128, 0, 0),    # Maroon
                    (128, 128, 0),  # Olive
                    (0, 128, 0),    # Dark Green
                    (128, 0, 128)   # Purple
                ]
    # Segment anything config 
    sam_file_url_b= "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth"
    sam_file_url_l = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_l_0b3195.pth"
    sam_file_url_h = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth"
    sam_model = {"model_type": "vit_b",
                 "file_url":sam_file_url_b}
    sam_weight_path = "sam_"+sam_model["model_type"]+".pth"
    sam_device = "cuda"
    sam_min_width = 25
    sam_max_width = 150

global_params = GlobalParams()

def download_weightfile(file_url,save_path):
    try: 
        subprocess.run(["wget", "-O", save_path, file_url], check=True)
        return 200
    except Exception as ex:
        return f"Could not download the file: {ex}", 500
    
def process_symbol() -> Tuple[str, int]:
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
        file_download_status =  download_weightfile(global_params.sam_model["file_url"],
                                               global_params.sam_weight_path)
    try:
        # Try to load the model
        sam = sam_model_registry[model_type](checkpoint=checkpoint)
    except:
        # Issue might the file was not downloaded, lets do that first in any case. 
        file_download_status =  download_weightfile(global_params.sam_model["file_url"],
                                               global_params.sam_weight_path)
        sam = sam_model_registry[model_type](checkpoint=checkpoint)
               
    sam.to(device=device)
    mask_generator = SamAutomaticMaskGenerator(
        model=sam,
        points_per_side=64,
        pred_iou_thresh=0.86,
        stability_score_thresh=0.92,
        crop_n_layers=1,
        crop_n_points_downscale_factor=2,
        min_mask_region_area=100,
    )

    try:
        save_symbols_path = "Results"
        # Read the image file
        image = cv2.imread("section_0_1.jpg")
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
        return "Image processed successfully", 200, file_paths
    except Exception as ex:
        return f"An error occurred: {ex}", 500
    

process_symbol()